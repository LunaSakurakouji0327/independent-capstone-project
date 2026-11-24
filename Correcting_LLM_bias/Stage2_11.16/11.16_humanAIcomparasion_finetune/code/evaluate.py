"""Compare every system with the human codes on the 100 reviews; 500 bootstrap resamples of reviews for 95% CIs.
Writes outputs/metrics.xlsx, outputs/metrics.json and figures in outputs/figures/."""
import json, random
from pathlib import Path
import numpy as np
from sklearn.metrics import cohen_kappa_score, f1_score
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"; (OUT / "figures").mkdir(parents=True, exist_ok=True)
B, SEED = 500, 2026
data = json.load(open(ROOT / "data" / "dataset.json", encoding="utf-8"))
C, ITEMS = data["constructs"], data["items"]
RIDS = [it["review_id"] for it in ITEMS]
gold = {(it["review_id"], c): it["labels"][c] for it in ITEMS for c in C}


def load_local(fn):
    return {(r["review_id"], r["construct"]): r["pred"] for r in map(json.loads, open(OUT / fn, encoding="utf-8"))}


def load_exp3(key):  # Exp3 sample_id is 0-based; human review_id = sample_id + 1
    d = {}
    for r in map(json.loads, open(ROOT / "data" / f"exp3_labels_{key}.jsonl", encoding="utf-8")):
        if r["label"] is not None:
            d[(r["review_id"] + 1, r["construct"])] = int(r["label"])
    return d


SYSTEMS = {
    "Qwen3-14B fine-tuned (5-fold CV)": load_local("predictions_finetuned.jsonl"),
    "Qwen3-14B zero-shot (same prompt v1)": load_local("predictions_zeroshot.jsonl"),
    "GPT-4o (prompt v2, Exp. 3)": load_exp3("gpt4o"),
    "Sonnet 5.5 (prompt v2, Exp. 3)": load_exp3("sonnet"),
    "Qwen3-14B Ollama (prompt v2, Exp. 3)": load_exp3("qwen"),
    "Gemma 3 12B (prompt v2, Exp. 3)": load_exp3("gemma"),
}
FT, ZS, GPT = list(SYSTEMS)[:3]


def metrics(sysd, c, rids):
    y, p = [], []
    for r in rids:
        g = gold[(r, c)]; q = sysd.get((r, c))
        if g is None or q is None:
            continue
        y.append(g); p.append(q)
    y, p = np.array(y), np.array(p)
    if len(y) == 0:
        return dict(kappa=np.nan, acc=np.nan, f1=np.nan, n=0)
    k = cohen_kappa_score(y, p) if len(set(y) | set(p)) > 1 else np.nan
    f1 = f1_score(y, p, zero_division=0) if y.sum() > 0 or p.sum() > 0 else np.nan
    return dict(kappa=k, acc=(y == p).mean(), f1=f1, n=len(y))


rng = random.Random(SEED)
boots = [[rng.choice(RIDS) for _ in RIDS] for _ in range(B)]

res = {}
for s, d in SYSTEMS.items():
    for c in C + ["Macro mean (excl. Change)"]:
        cs = [x for x in C if x != "Change"] if c.startswith("Macro") else [c]
        pt = {m: np.nanmean([metrics(d, x, RIDS)[m] for x in cs]) for m in ("kappa", "acc", "f1")}
        bs = {m: [] for m in pt}
        for br in boots:
            ms = [metrics(d, x, br) for x in cs]
            for m in pt:
                v = [mm[m] for mm in ms]
                bs[m].append(np.nan if all(np.isnan(v)) else np.nanmean(v))
        res[(s, c)] = {m: (pt[m], np.nanpercentile(bs[m], 2.5), np.nanpercentile(bs[m], 97.5), int(np.isnan(bs[m]).sum())) for m in pt}
        res[(s, c)]["n"] = metrics(d, cs[0], RIDS)["n"]
        res[(s, c)]["_boot_kappa"] = bs["kappa"]

# paired differences in kappa
diffs = {}
for other in (ZS, GPT):
    for c in C + ["Macro mean (excl. Change)"]:
        a = np.array(res[(FT, c)]["_boot_kappa"]); b = np.array(res[(other, c)]["_boot_kappa"])
        dd = a - b
        pt = res[(FT, c)]["kappa"][0] - res[(other, c)]["kappa"][0]
        diffs[(other, c)] = (pt, np.nanpercentile(dd, 2.5), np.nanpercentile(dd, 97.5), float(np.nanmean(dd > 0)))

prev = {c: (sum(1 for r in RIDS if gold[(r, c)] == 1), sum(1 for r in RIDS if gold[(r, c)] is not None)) for c in C}

# ---- excel ----
wb = Workbook(); hf = Font(bold=True, color="FFFFFF"); fill = PatternFill("solid", fgColor="1F3864")
def hdr(ws):
    for cell in ws[1]:
        cell.font = hf; cell.fill = fill; cell.alignment = Alignment(wrap_text=True, vertical="center")
    ws.row_dimensions[1].height = 40
ws = wb.active; ws.title = "Kappa vs human"
ws.append(["System", "Construct", "N", "Human % 1", "κ", "κ 95% CI low", "κ 95% CI high", "Accuracy", "Acc CI low", "Acc CI high", "F1 (class 1)", "F1 CI low", "F1 CI high", "Bootstrap draws with undefined κ"])
for (s, c), v in res.items():
    pv = prev.get(c)
    ws.append([s, c, v["n"], round(pv[0] / pv[1], 3) if pv else None] + [round(x, 3) for x in v["kappa"][:3]] + [round(x, 3) for x in v["acc"][:3]] + [round(x, 3) for x in v["f1"][:3]] + [v["kappa"][3]])
hdr(ws); ws.column_dimensions["A"].width = 38; ws.column_dimensions["B"].width = 28
ws2 = wb.create_sheet("Fine-tuned minus other")
ws2.append(["Comparison", "Construct", "Δκ", "Δκ CI low", "Δκ CI high", "P(Δκ > 0) in bootstrap"])
for (o, c), v in diffs.items():
    ws2.append([f"Fine-tuned − {o}", c] + [round(x, 3) for x in v])
hdr(ws2); ws2.column_dimensions["A"].width = 50; ws2.column_dimensions["B"].width = 28
ws3 = wb.create_sheet("Method")
for row in [("Data", "human_coding_100_finished.xlsx: 100 reviews × 7 constructs (Change: 2 blank cells excluded)"),
            ("Cross-validation", f"Stratified 5-fold (split seed {data['split_seed']}); each review predicted once by a model that never saw it"),
            ("Bootstrap", f"{B} resamples of the 100 reviews with replacement (seed {SEED}); percentile 95% CI; paired across systems"),
            ("Macro mean", "Mean over 6 constructs; Change excluded (3 positives in 98 coded reviews)"),
            ("Exp. 3 systems", "Labels from the earlier 4-model run on the same reviews (prompt v2 with examples, zero-shot)")]:
    ws3.append(list(row))
ws3.column_dimensions["A"].width = 20; ws3.column_dimensions["B"].width = 120
wb.save(OUT / "metrics.xlsx")

json.dump({"kappa": {f"{s} | {c}": v["kappa"][:3] for (s, c), v in res.items()},
           "accuracy": {f"{s} | {c}": v["acc"][:3] for (s, c), v in res.items()},
           "f1": {f"{s} | {c}": v["f1"][:3] for (s, c), v in res.items()},
           "diff_kappa": {f"FT - {o} | {c}": v for (o, c), v in diffs.items()},
           "prevalence": prev}, open(OUT / "metrics.json", "w"), indent=1, default=float)

# ---- figure: forest plot of kappa ----
names = list(SYSTEMS)
colors = ["#1F3864", "#8FAADC", "#C55A11", "#7F7F7F", "#A9D18E", "#BF9000"]
cs = C[:-1] + ["Macro mean (excl. Change)"]
fig, ax = plt.subplots(figsize=(8.5, 7.5))
for ci, c in enumerate(cs):
    for si, s in enumerate(names):
        y = ci * (len(names) + 1.5) + si
        k, lo, hi, _ = res[(s, c)]["kappa"]
        ax.errorbar(k, -y, xerr=[[k - lo], [hi - k]], fmt="o", color=colors[si], ms=5, capsize=2, lw=1.2, label=s if ci == 0 else None)
ax.set_yticks([-(ci * (len(names) + 1.5) + (len(names) - 1) / 2) for ci in range(len(cs))])
ax.set_yticklabels(cs)
ax.axvline(0, color="black", lw=0.6); ax.set_xlim(-0.6, 1.0)
for x in (0.2, 0.4, 0.6, 0.8): ax.axvline(x, color="#DDDDDD", lw=0.6, zorder=0)
ax.set_xlabel("Cohen's κ vs human codes (95% bootstrap CI, 500 resamples)")
ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, fontsize=8, frameon=False)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.savefig(OUT / "figures" / "kappa_forest.png", dpi=200); plt.close()

# training loss figure
logp = OUT / "training_log.jsonl"
if logp.exists():
    lg = [json.loads(l) for l in open(logp)]
    fig, ax = plt.subplots(figsize=(7, 3.2))
    for k in sorted({r["fold"] for r in lg}):
        rr = [r for r in lg if r["fold"] == k]
        ax.plot([r["step"] for r in rr], [r["loss"] for r in rr], lw=1, label=f"fold {k+1}")
    ax.set_xlabel("optimizer step"); ax.set_ylabel("training loss (answer tokens)")
    ax.legend(fontsize=8, ncol=5, frameon=False); ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout(); plt.savefig(OUT / "figures" / "training_loss.png", dpi=200); plt.close()

print("prevalence", prev)
for c in cs:
    print(c)
    for s in names:
        k, lo, hi, nn = res[(s, c)]["kappa"]; a = res[(s, c)]["acc"][0]
        print(f"   {s:40s} κ {k:6.3f} [{lo:6.3f},{hi:6.3f}]  acc {a:.2f}  undefined {nn}")
for (o, c), v in diffs.items():
    if c.startswith("Macro"): print(f"FT − {o}: Δκ {v[0]:.3f} [{v[1]:.3f},{v[2]:.3f}] P>0 {v[3]:.2f}")
