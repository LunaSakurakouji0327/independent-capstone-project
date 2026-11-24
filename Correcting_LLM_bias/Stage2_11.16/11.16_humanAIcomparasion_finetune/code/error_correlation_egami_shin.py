"""Conditional error (residual) correlation between LLM annotators, following Egami & Shin (2026),
'Debiased Inference for AI-Generated Data without Gold-Standard Labels', Sec. 3.1 (Assumption 3.1) and Sec. 5.3.

Assumption: X(1) _||_ ... _||_ X(J) | X, D. With gold labels for all units (R=1, pi=1) the pairwise implication is
    E[ 1{X=a} h(D) (X(j) - pi_{j,a}(D)) (X(k) - pi_{k,a}(D)) ] = 0,   a in {0,1}
i.e. zero covariance of the two models' residuals within each true class (and within D strata).
We report the class-conditional residual correlation and test it with stratified permutation tests
(each model's labels permuted independently within (X, D) strata, which preserves pi_{j,a}(D) and breaks dependence)."""
import json, itertools
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "error_correlation"; OUT.mkdir(parents=True, exist_ok=True)
NPERM, SEED = 2000, 2026
rng = np.random.default_rng(SEED)
data = json.load(open(ROOT / "data" / "dataset.json", encoding="utf-8"))
C, ITEMS = data["constructs"], data["items"]
MODELS = {"GPT-4o": "gpt4o", "Sonnet 5.5": "sonnet", "Qwen3-14B": "qwen", "Gemma 3 12B": "gemma"}
names = list(MODELS)
pairs = list(itertools.combinations(range(len(names)), 2))
lab = {}
for m, k in MODELS.items():
    for r in map(json.loads, open(ROOT / "data" / f"exp3_labels_{k}.jsonl", encoding="utf-8")):
        if r["label"] is not None:
            lab[(m, r["review_id"] + 1, r["construct"])] = int(r["label"])

# D: review length tertile (a simple task-difficulty covariate, Sec. 5.1)
wl = {it["review_id"]: len(it["text"].split()) for it in ITEMS}
cuts = np.quantile(list(wl.values()), [1 / 3, 2 / 3])
dlen = {r: int(np.searchsorted(cuts, v, side="right")) for r, v in wl.items()}


def residual_corr(L, strata):
    """L: n x J labels, strata: n stratum ids. Residuals = label - stratum mean (estimate of pi_{j,a}(D)).
    Returns J x J correlation of residuals (NaN when a model has no variation)."""
    R = L.astype(float).copy()
    for s in np.unique(strata):
        idx = strata == s
        R[idx] -= R[idx].mean(0)
    J = L.shape[1]; out = np.full((J, J), np.nan)
    sd = np.sqrt((R ** 2).mean(0))
    for j, k in pairs:
        if sd[j] > 0 and sd[k] > 0:
            out[j, k] = out[k, j] = (R[:, j] * R[:, k]).mean() / (sd[j] * sd[k])
    return out


def perm_test(L, strata):
    obs = residual_corr(L, strata)
    cnt = np.zeros_like(obs); joint_obs = np.nansum(np.square([obs[j, k] for j, k in pairs])); jc = 0
    for _ in range(NPERM):
        P = L.copy()
        for s in np.unique(strata):
            idx = np.where(strata == s)[0]
            for j in range(L.shape[1]):
                P[idx, j] = L[rng.permutation(idx), j]
        pc = residual_corr(P, strata)
        cnt += np.abs(pc) >= np.abs(obs) - 1e-12
        jc += np.nansum(np.square([pc[j, k] for j, k in pairs])) >= joint_obs - 1e-12
    return obs, (cnt + 1) / (NPERM + 1), (jc + 1) / (NPERM + 1)


rows, joint = [], []
for c in C:
    rids = [it["review_id"] for it in ITEMS if it["labels"][c] is not None]
    X = np.array([next(it["labels"][c] for it in ITEMS if it["review_id"] == r) for r in rids])
    L = np.array([[lab[(m, r, c)] for m in names] for r in rids])
    for spec, D in (("X only", np.zeros(len(rids), int)), ("X + length tertile", np.array([dlen[r] for r in rids]))):
        for a in (0, 1):
            idx = X == a
            if idx.sum() < 3:
                continue
            obs, p, pj = perm_test(L[idx], D[idx] if spec != "X only" else np.zeros(idx.sum(), int))
            err = (L[idx] != a).mean(0)
            joint.append({"construct": c, "conditioning": spec, "true_class": a, "n": int(idx.sum()), "joint_p": float(pj)})
            for j, k in pairs:
                both = int(((L[idx][:, j] != a) & (L[idx][:, k] != a)).sum())
                exp = float(err[j] * err[k] * idx.sum())
                rows.append({"construct": c, "conditioning": spec, "true_class": a, "n": int(idx.sum()),
                             "model_A": names[j], "model_B": names[k], "err_rate_A": float(err[j]), "err_rate_B": float(err[k]),
                             "both_wrong": both, "both_wrong_if_independent": round(exp, 2),
                             "resid_corr": None if np.isnan(obs[j, k]) else float(obs[j, k]), "perm_p": float(p[j, k])})

# Benjamini-Hochberg within each conditioning spec (pairwise tests with defined correlation)
for spec in ("X only", "X + length tertile"):
    rs = [r for r in rows if r["conditioning"] == spec and r["resid_corr"] is not None]
    ps = np.array([r["perm_p"] for r in rs]); o = np.argsort(ps); m = len(ps)
    q = np.minimum.accumulate((ps[o] * m / np.arange(1, m + 1))[::-1])[::-1]
    for i, oi in enumerate(o):
        rs[oi]["bh_q"] = float(min(q[i], 1))
json.dump({"pairwise": rows, "joint": joint, "nperm": NPERM, "seed": SEED, "length_cuts_words": cuts.tolist()},
          open(OUT / "error_correlation.json", "w"), indent=1)

# pooled summary per pair: n-weighted mean residual correlation over 6 constructs (excl. Change), X-only spec
summ = {}
for j, k in pairs:
    for a in (0, 1):
        rr = [r for r in rows if r["conditioning"] == "X only" and r["true_class"] == a and r["model_A"] == names[j] and r["model_B"] == names[k]
              and r["construct"] != "Change" and r["resid_corr"] is not None]
        w = np.array([r["n"] for r in rr]); v = np.array([r["resid_corr"] for r in rr])
        summ[(names[j], names[k], a)] = float((w * v).sum() / w.sum())

# Excel
wb = Workbook(); hf = Font(bold=True, color="FFFFFF"); fill = PatternFill("solid", fgColor="1F3864")
def hdr(ws, widths):
    for cell in ws[1]:
        cell.font = hf; cell.fill = fill; cell.alignment = Alignment(wrap_text=True, vertical="center")
    for i, w in enumerate(widths, 1): ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 36; ws.freeze_panes = "A2"
ws = wb.active; ws.title = "Pairwise residual corr"
keys = ["construct", "conditioning", "true_class", "n", "model_A", "model_B", "err_rate_A", "err_rate_B", "both_wrong", "both_wrong_if_independent", "resid_corr", "perm_p", "bh_q"]
ws.append(keys)
for r in rows:
    ws.append([round(r.get(k), 3) if isinstance(r.get(k), float) else r.get(k) for k in keys])
hdr(ws, [24, 18, 10, 6, 12, 12, 10, 10, 10, 12, 11, 9, 9])
ws2 = wb.create_sheet("Joint test per class")
ws2.append(["construct", "conditioning", "true_class", "n", "joint permutation p (sum of squared pairwise residual corr)"])
for r in joint: ws2.append([r["construct"], r["conditioning"], r["true_class"], r["n"], round(r["joint_p"], 4)])
hdr(ws2, [24, 18, 10, 6, 40])
ws3 = wb.create_sheet("Pooled by pair")
ws3.append(["model_A", "model_B", "mean resid corr | human=0 (6 constructs, n-weighted)", "mean resid corr | human=1"])
for j, k in pairs:
    ws3.append([names[j], names[k], round(summ[(names[j], names[k], 0)], 3), round(summ[(names[j], names[k], 1)], 3)])
hdr(ws3, [14, 14, 30, 30])
ws4 = wb.create_sheet("Method")
for t in ["Egami & Shin (2026) Assumption 3.1: model labels independent given the true label X and covariates D.",
          "Sec. 5.3 residual moment: E[1{X=a} h(D) (X(j)-pi_j,a(D))(X(k)-pi_k,a(D))] = 0, tested here with h = 1.",
          "Human codes used as X for all 100 reviews (R = 1, pi = 1). pi_j,a(D) estimated by the stratum mean of model j within class a (and D stratum).",
          "resid_corr = correlation of residuals within true class a; >0 means the two models tend to err on the same reviews beyond what their error rates imply.",
          f"Permutation test: {NPERM} draws, each model's labels permuted independently within (X, D) strata; two-sided on |corr|; BH q-values within each conditioning spec.",
          f"D = review length tertile (cut points {cuts[0]:.0f} and {cuts[1]:.0f} words).",
          "Correlation undefined (blank) when a model makes no errors / no variation within the class."]:
    ws4.append([t])
ws4.column_dimensions["A"].width = 150
wb.save(OUT / "error_correlation_egami_shin.xlsx")

# heatmap figure: X-only, per construct, class 0 and class 1
cs = [c for c in C if c != "Change"]
fig, axes = plt.subplots(2, len(cs), figsize=(16, 5.6))
short = ["GPT", "Son", "Qwen", "Gem"]
for col, c in enumerate(cs):
    for a in (0, 1):
        M = np.full((4, 4), np.nan)
        for r in rows:
            if r["construct"] == c and r["conditioning"] == "X only" and r["true_class"] == a and r["resid_corr"] is not None:
                j, k = names.index(r["model_A"]), names.index(r["model_B"]); M[j, k] = M[k, j] = r["resid_corr"]
        ax = axes[a, col]; im = ax.imshow(M, cmap="RdBu_r", vmin=-1, vmax=1)
        for j in range(4):
            for k in range(4):
                if j != k and not np.isnan(M[j, k]):
                    sig = next((r for r in rows if r["construct"] == c and r["conditioning"] == "X only" and r["true_class"] == a
                                and {r["model_A"], r["model_B"]} == {names[j], names[k]}), None)
                    star = "*" if sig and sig.get("bh_q", 1) < 0.05 else ""
                    ax.text(k, j, f"{M[j,k]:.2f}{star}", ha="center", va="center", fontsize=7)
        ax.set_xticks(range(4)); ax.set_yticks(range(4)); ax.set_xticklabels(short, fontsize=7); ax.set_yticklabels(short, fontsize=7)
        n = sum(1 for it in ITEMS if it["labels"][c] == a)
        ax.set_title(f"{c.replace('Absence of ', '')}\nhuman={a} (n={n})", fontsize=8)
fig.colorbar(im, ax=axes, shrink=0.6, label="residual correlation within true class")
fig.suptitle("Conditional error correlation between LLM annotators (Egami & Shin 2026, Sec. 5.3); * = BH q < 0.05", fontsize=10)
plt.savefig(OUT / "residual_corr_heatmaps.png", dpi=170, bbox_inches="tight"); plt.close()

# console summary
print("pooled residual correlation by pair (X only, 6 constructs, n-weighted):")
for j, k in pairs:
    print(f"  {names[j]:11s} – {names[k]:11s}  | human=0: {summ[(names[j], names[k], 0)]:.3f}   | human=1: {summ[(names[j], names[k], 1)]:.3f}")
for spec in ("X only", "X + length tertile"):
    rs = [r for r in rows if r["conditioning"] == spec and r["resid_corr"] is not None]
    print(f"{spec}: {len(rs)} pairwise tests; p<0.05: {sum(r['perm_p']<0.05 for r in rs)}; BH q<0.05: {sum(r['bh_q']<0.05 for r in rs)}; "
          f"positive corr: {sum(r['resid_corr']>0 for r in rs)}; joint tests p<0.05: {sum(1 for r in joint if r['conditioning']==spec and r['joint_p']<0.05)}/{sum(1 for r in joint if r['conditioning']==spec)}")
print("per construct (X only), mean resid corr over pairs; joint p:")
for c in C:
    for a in (0, 1):
        rr = [r for r in rows if r["construct"] == c and r["conditioning"] == "X only" and r["true_class"] == a and r["resid_corr"] is not None]
        jp = next((r["joint_p"] for r in joint if r["construct"] == c and r["conditioning"] == "X only" and r["true_class"] == a), None)
        if rr:
            print(f"  {c:26s} human={a} n={rr[0]['n']:3d}  mean corr {np.mean([r['resid_corr'] for r in rr]):6.3f}  "
                  f"range [{min(r['resid_corr'] for r in rr):.2f},{max(r['resid_corr'] for r in rr):.2f}]  sig(BH) {sum(r['bh_q']<0.05 for r in rr)}/{len(rr)}  joint p {jp:.4f}")
