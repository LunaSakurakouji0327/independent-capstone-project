"""Conditional-independence (CI) diagnostics for DMM (Egami & Shin 2026, arXiv 2608.18294v2) and per-construct proxy selection.
A. Direct test with gold labels (Sec. 5.3), 100 human-coded reviews: class-conditional residual correlation of every model pair
   within strata of (X*, D), D = review-length tertile; stratified permutation p-values (labels permuted independently within strata).
B. No-gold diagnostics (Sec. 5.2), 150 new reviews, 5 models: (i) overidentification test of the 2-class product-mixture
   (Dawid-Skene) model, parametric-bootstrap deviance (2^5-1-11 = 20 restrictions); (ii) subset diagnostic: prevalence
   P(X*=1) identified from each of the 10 three-model subsets should agree; centered-bootstrap heterogeneity test.
C. Per-construct triples: gold kappa vs human + max residual correlation (A) + subset estimates (B).
Writes CI_DMM_results.xlsx and outputs/ci_dmm.json."""
import json, itertools
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.metrics import cohen_kappa_score
D = Path(__file__).resolve().parent.parent; F = D.parent / "11.16_humanAIcomparasion_finetune"
B = D.parent.parent
C = ["Absence of Naive Realism", "Theme", "Thought-Provoking", "Ease", "Critic", "Surprise", "Change"]; C6 = C[:6]
rng = np.random.default_rng(2026); NPERM, NBOOT = 2000, 400
ds = json.load(open(F / "data" / "dataset.json", encoding="utf-8")); ITEMS = ds["items"]
gold = {(it["review_id"], c): it["labels"][c] for it in ITEMS for c in C}
wl = {it["review_id"]: len(it["text"].split()) for it in ITEMS}; cuts = np.quantile(list(wl.values()), [1 / 3, 2 / 3])
dlen = {r: int(np.searchsorted(cuts, v, side="right")) for r, v in wl.items()}

# ---------- gold-sample labels ----------
G = {}
for name, k in [("GPT-4o (v2)", "gpt4o"), ("Sonnet 5.5 (v2)", "sonnet"), ("Qwen3-14B Ollama (v2)", "qwen"), ("Gemma 3 12B (v2)", "gemma")]:
    for r in map(json.loads, open(F / "data" / f"exp3_labels_{k}.jsonl", encoding="utf-8")):
        if r["label"] is not None: G[(name, r["review_id"] + 1, r["construct"])] = int(r["label"])
for r in map(json.loads, open(F / "outputs" / "predictions_finetuned.jsonl", encoding="utf-8")):
    G[("Qwen3-14B fine-tuned (CV, v1)", r["review_id"], r["construct"])] = int(r["pred"])
for name, k in [("GPT-6 Luna (v2/v3/v4)", "luna"), ("GPT-5.4 mini (v2/v3/v4)", "mini")]:
    for r in map(json.loads, open(D / "outputs" / f"gold_progress_{k}.jsonl", encoding="utf-8")):
        if r["label"] is not None: G[(name, r["sample_id"], r["construct"])] = int(r["label"])
GM = ["GPT-4o (v2)", "Sonnet 5.5 (v2)", "Qwen3-14B Ollama (v2)", "Gemma 3 12B (v2)", "Qwen3-14B fine-tuned (CV, v1)", "GPT-6 Luna (v2/v3/v4)", "GPT-5.4 mini (v2/v3/v4)"]
S5_GOLD = {"Sonnet 5.5": "Sonnet 5.5 (v2)", "Gemma 3 12B": "Gemma 3 12B (v2)", "Qwen3-14B fine-tuned": "Qwen3-14B fine-tuned (CV, v1)",
           "GPT-6 Luna": "GPT-6 Luna (v2/v3/v4)", "GPT-5.4 mini": "GPT-5.4 mini (v2/v3/v4)"}

def resid(x, strata):
    r = x.astype(float).copy()
    for s in np.unique(strata):
        i = strata == s; r[i] -= r[i].mean()
    return r

def pair_test(a, b, strata):
    ra, rb = resid(a, strata), resid(b, strata); den = np.sqrt((ra ** 2).mean() * (rb ** 2).mean())
    if den == 0: return np.nan, np.nan, len(a)
    obs = (ra * rb).mean() / den; cnt = 0
    for _ in range(NPERM):
        pa = a.copy()
        for s in np.unique(strata):
            i = np.where(strata == s)[0]; pa[i] = rng.permutation(pa[i])
        rp = resid(pa, strata); cnt += abs((rp * rb).mean() / den) >= abs(obs) - 1e-12
    return obs, (cnt + 1) / (NPERM + 1), len(a)

A = []
for c in C6:
    for m1, m2 in itertools.combinations(GM, 2):
        ids = [i for i in range(1, 110) if (i, c) in gold and gold[(i, c)] is not None and (m1, i, c) in G and (m2, i, c) in G]
        a = np.array([G[(m1, i, c)] for i in ids]); b = np.array([G[(m2, i, c)] for i in ids])
        st = np.array([gold[(i, c)] * 3 + dlen[i] for i in ids])
        rho, p, n = pair_test(a, b, st)
        A.append({"construct": c, "model 1": m1, "model 2": m2, "n": n, "residual corr | X*, length": rho, "perm p": p})
A = pd.DataFrame(A)
A["q (BH, within construct)"] = np.nan
for c in C6:
    i = A.index[(A.construct == c) & A["perm p"].notna()]; p = A.loc[i, "perm p"].values; o = np.argsort(p); m = len(p)
    q = np.minimum.accumulate((p[o] * m / np.arange(1, m + 1))[::-1])[::-1]; A.loc[i[o], "q (BH, within construct)"] = np.minimum(q, 1)
kap = pd.DataFrame({m: {c: cohen_kappa_score(*zip(*[(gold[(i, c)], G[(m, i, c)]) for i in range(1, 110)
                    if (i, c) in gold and gold[(i, c)] is not None and (m, i, c) in G])) for c in C6} for m in GM})

# ---------- B: 150 new reviews, 5 models ----------
NM = {"sonnet": "Sonnet 5.5", "gemma": "Gemma 3 12B", "qwenft": "Qwen3-14B fine-tuned", "luna": "GPT-6 Luna", "mini": "GPT-5.4 mini"}
L = {}
for k, n in NM.items():
    for r in map(json.loads, open(D / "outputs" / f"progress_{k}.jsonl", encoding="utf-8")):
        if k == "qwenft": L[(n, r["review_id"], r["construct"])] = int(r["pred"])
        elif r["label"] is not None: L[(n, r["sample_id"], r["construct"])] = int(r["label"])
M5 = list(NM.values()); ids150 = sorted({k[1] for k in L})

def em(X, iters=500):
    """Binary 2-class latent class model. Returns pi=P(X*=1), se (P(x=1|X*=1)), fp (P(x=1|X*=0)), loglik."""
    n, J = X.shape; pi, se, fp = 0.3, np.full(J, 0.8), np.full(J, 0.1)
    for _ in range(iters):
        l1 = pi * np.prod(se ** X * (1 - se) ** (1 - X), 1); l0 = (1 - pi) * np.prod(fp ** X * (1 - fp) ** (1 - X), 1)
        w = l1 / (l1 + l0)
        pi = np.clip(w.mean(), 1e-4, 1 - 1e-4)
        se = np.clip((w[:, None] * X).sum(0) / w.sum(), 1e-4, 1 - 1e-4); fp = np.clip(((1 - w)[:, None] * X).sum(0) / (1 - w).sum(), 1e-4, 1 - 1e-4)
    if np.mean(se - fp) < 0: pi, se, fp = 1 - pi, fp, se  # label switching: class 1 = class with higher P(code 1)
    return pi, se, fp, np.log(l1 + l0).sum()

def pattern_probs(pi, se, fp, J):
    pats = np.array(list(itertools.product([0, 1], repeat=J)))
    return pats, pi * np.prod(se ** pats * (1 - se) ** (1 - pats), 1) + (1 - pi) * np.prod(fp ** pats * (1 - fp) ** (1 - pats), 1)

def deviance(X, pats, p):
    obs = np.array([(X == q).all(1).sum() for q in pats]); exp = p * len(X); m = obs > 0
    return 2 * (obs[m] * np.log(obs[m] / exp[m])).sum()

Bres, Sres = [], []
for c in C6:
    X = np.array([[L[(m, i, c)] for m in M5] for i in ids150])
    pi, se, fp, _ = em(X); pats, p = pattern_probs(pi, se, fp, 5); dev = deviance(X, pats, p)
    bd = []
    for _ in range(NBOOT):
        z = rng.random(len(X)) < pi
        Xb = np.where(z[:, None], rng.random(X.shape) < se, rng.random(X.shape) < fp).astype(int)
        pb, sb, fb, _ = em(Xb, 200); pp, qq = pattern_probs(pb, sb, fb, 5); bd.append(deviance(Xb, pp, qq))
    Bres.append({"construct": c, "prevalence (5-model LCM)": pi, "deviance": dev, "bootstrap p (overidentification)": (np.sum(np.array(bd) >= dev) + 1) / (NBOOT + 1),
                 **{f"sens {m}": s for m, s in zip(M5, se)}, **{f"FPR {m}": f for m, f in zip(M5, fp)}})
    trip = list(itertools.combinations(range(5), 3))
    est = np.array([em(X[:, list(t)], 300)[0] for t in trip])
    boot = []
    for _ in range(NBOOT // 2):
        Xb = X[rng.integers(0, len(X), len(X))]; boot.append([em(Xb[:, list(t)], 200)[0] for t in trip])
    boot = np.array(boot); T = ((est - est.mean()) ** 2).sum(); dev_b = (boot - est); Tb = ((dev_b - dev_b.mean(1, keepdims=True)) ** 2).sum(1)
    for t, e, lo, hi in zip(trip, est, np.percentile(boot, 2.5, 0), np.percentile(boot, 97.5, 0)):
        Sres.append({"construct": c, "triple": " + ".join(M5[j] for j in t), "prevalence": e, "boot 2.5%": lo, "boot 97.5%": hi,
                     "heterogeneity p (construct)": (np.sum(Tb >= T) + 1) / (len(Tb) + 1)})
Bres, Sres = pd.DataFrame(Bres), pd.DataFrame(Sres)

# ---------- C: per-construct triples among the 5 Stage-3 models ----------
Cres = []
for c in C6:
    sub = A[A.construct == c]
    for t in itertools.combinations(M5, 3):
        g = [S5_GOLD[m] for m in t]
        rr = sub[(sub["model 1"].isin(g)) & (sub["model 2"].isin(g))]
        fam = len({("GPT" if "GPT" in m else "Qwen" if "Qwen" in m else m) for m in t})
        pk = np.mean([cohen_kappa_score([L[(a, i, c)] for i in ids150], [L[(b, i, c)] for i in ids150]) for a, b in itertools.combinations(t, 2)])
        Cres.append({"construct": c, "triple": " + ".join(t), "distinct families": fam, "min kappa vs human (gold)": min(kap.loc[c, g]),
                     "mean kappa vs human (gold)": float(np.mean(kap.loc[c, g])), "max |residual corr| (gold)": rr["residual corr | X*, length"].abs().max(),
                     "min perm p (gold)": rr["perm p"].min(), "mean pairwise kappa (150 new)": pk})
Cres = pd.DataFrame(Cres)
with pd.ExcelWriter(D / "CI_DMM_results.xlsx") as w:
    A.to_excel(w, sheet_name="A gold residual corr", index=False); kap.to_excel(w, sheet_name="A gold kappa vs human")
    Bres.to_excel(w, sheet_name="B overidentification", index=False); Sres.to_excel(w, sheet_name="B subset prevalence", index=False)
    Cres.to_excel(w, sheet_name="C triples", index=False)
json.dump({"A": A.to_dict("records"), "kap": kap.to_dict(), "B": Bres.to_dict("records"), "S": Sres.to_dict("records"), "C": Cres.to_dict("records")},
          open(D / "outputs" / "ci_dmm.json", "w"), indent=1, default=float)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 500)
print("== A: share of pairs with perm p<0.05 / BH q<0.10, per construct (all 7 gold models, 21 pairs)")
print(A.groupby("construct").apply(lambda d: pd.Series({"pairs": d["perm p"].notna().sum(), "p<.05": (d["perm p"] < .05).sum(),
      "q<.10": (d["q (BH, within construct)"] < .10).sum(), "median rho": d["residual corr | X*, length"].median()}), include_groups=False).to_string())
s5 = A[A["model 1"].isin(S5_GOLD.values()) & A["model 2"].isin(S5_GOLD.values())]
print("== A restricted to the 5 Stage-3 models (10 pairs)")
print(s5.groupby("construct").apply(lambda d: pd.Series({"p<.05": (d["perm p"] < .05).sum(), "median rho": d["residual corr | X*, length"].median(),
      "max rho": d["residual corr | X*, length"].max()}), include_groups=False).to_string())
print("== kappa vs human (gold)"); print(kap.round(2).to_string())
print("== B"); print(Bres[["construct", "prevalence (5-model LCM)", "deviance", "bootstrap p (overidentification)"]].round(3).to_string(index=False))
print(Sres.groupby("construct").agg(min_prev=("prevalence", "min"), max_prev=("prevalence", "max"), p=("heterogeneity p (construct)", "first")).round(3).to_string())
print("== C best triples (>=3 families? sorted by max residual corr)")
for c in C6:
    d = Cres[Cres.construct == c].sort_values(["max |residual corr| (gold)"]).head(3)
    print(d[["construct", "triple", "distinct families", "min kappa vs human (gold)", "max |residual corr| (gold)", "mean pairwise kappa (150 new)"]].round(2).to_string(index=False, header=False))
