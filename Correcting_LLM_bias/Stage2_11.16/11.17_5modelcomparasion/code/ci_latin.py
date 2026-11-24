"""Group-level conditional independence (Egami & Shin 2026, Sec. 5.1): groups = Sonnet | Gemma | Qwen-FT | GPT (Luna + 5.4 mini).
Dependence inside the GPT group is allowed; CI is required only BETWEEN groups. D = embedding PCs + each model's own prompt.
Compares the earlier design (prompts randomised independently per model) with the Latin-square design
(on every review Sonnet, Gemma and GPT get three different prompts).
A. Gold sample (100 reviews): cross-fitted residual moments for every between-group model pair (Sec. 5.3).
   NB earlier design on the gold sample = Experiment 3 Sonnet/Gemma (prompt v2 for all reviews) + random Luna/mini.
B. New sample (150 reviews): group latent class model with covariates; GPT group modelled as P(Luna|X*,D) * P(mini|X*,D,Luna).
   (i) between-group bivariate-residual overidentification test (parametric bootstrap); (ii) prevalence from each of the
   4 three-group subsets, centered bootstrap heterogeneity test.
Writes CI_latin_results.xlsx and outputs/ci_latin.json."""
import json, itertools, time, csv
from math import erf, sqrt
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.decomposition import PCA
D0 = Path(__file__).resolve().parent.parent; F = D0.parent / "11.16_humanAIcomparasion_finetune"; O = D0 / "outputs"
C6 = ["Absence of Naive Realism", "Theme", "Thought-Provoking", "Ease", "Critic", "Surprise"]
rng = np.random.default_rng(2026)
Z = np.load(O / "embeddings.npz"); pca = PCA(40, random_state=0).fit(np.vstack([Z["E_gold"], Z["E_new"]]))
PG = {int(i): r for i, r in zip(Z["ids_gold"], pca.transform(Z["E_gold"]))}; PN = {int(i): r for i, r in zip(Z["ids_new"], pca.transform(Z["E_new"]))}
sig = lambda v: 1 / (1 + np.exp(-np.clip(v, -30, 30)))
pval = lambda z: 2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2))))
std = lambda P: (P - P.mean(0)) / P.std(0)
dummies = lambda pr: np.column_stack([np.array(pr) == "v3", np.array(pr) == "v4"]).astype(float)
MODELS = ["Sonnet 5.5", "Gemma 3 12B", "Qwen3-14B fine-tuned", "GPT-6 Luna", "GPT-5.4 mini"]
GROUP = {"Sonnet 5.5": "Sonnet", "Gemma 3 12B": "Gemma", "Qwen3-14B fine-tuned": "Qwen-FT", "GPT-6 Luna": "GPT", "GPT-5.4 mini": "GPT"}
KEY = {"Sonnet 5.5": "sonnet", "Gemma 3 12B": "gemma", "GPT-6 Luna": "luna", "GPT-5.4 mini": "mini"}

def ridge_logit(X, y, w=None, lam=1.0, beta=None, iters=25):
    n, p = X.shape; w = np.ones(n) if w is None else w; b = np.zeros(p) if beta is None else beta.copy()
    P = lam * np.eye(p); P[0, 0] = 0
    for _ in range(iters):
        mu = sig(X @ b); s = w * mu * (1 - mu) + 1e-9
        step = np.linalg.solve(X.T @ (X * s[:, None]) + P, X.T @ (w * (y - mu)) - P @ b); b += step
        if np.abs(step).max() < 1e-6: break
    return b

def load(design, gold):
    """Returns labels L[(model, id, construct)] and prompts PR[(model, id)]."""
    L, PR = {}, {}
    for m, k in KEY.items():
        if gold and design == "random" and k in ("sonnet", "gemma"):
            for r in map(json.loads, open(F / "data" / f"exp3_labels_{k}.jsonl", encoding="utf-8")):
                if r["label"] is not None: L[(m, r["review_id"] + 1, r["construct"])] = int(r["label"]); PR[(m, r["review_id"] + 1)] = "v2"
            continue
        f = O / (("gold_" if gold else "") + ("latin_" if design == "latin" else "") + f"progress_{k}.jsonl")
        for r in map(json.loads, open(f, encoding="utf-8")):
            if r["label"] is not None: L[(m, r["sample_id"], r["construct"])] = int(r["label"]); PR[(m, r["sample_id"])] = r["prompt"]
    q = F / "outputs" / "predictions_finetuned.jsonl" if gold else O / "progress_qwenft.jsonl"
    for r in map(json.loads, open(q, encoding="utf-8")):
        L[("Qwen3-14B fine-tuned", r["review_id"], r["construct"])] = int(r["pred"]); PR[("Qwen3-14B fine-tuned", r["review_id"])] = "v1"
    return L, PR

# ---------------- A: gold ----------------
ds = json.load(open(F / "data" / "dataset.json", encoding="utf-8")); gold = {(it["review_id"], c): it["labels"][c] for it in ds["items"] for c in C6}
def crossfit_resid(Xd, x, cls, lam=2.0, reps=5):
    eta = np.zeros(len(x))
    for r in range(reps):
        fold = np.random.default_rng(100 + r).permutation(len(x)) % 5
        for f in range(5):
            for a in (0, 1):
                tr = (fold != f) & (cls == a); te = (fold == f) & (cls == a)
                if te.sum() == 0: continue
                y = x[tr]
                if tr.sum() < 3 or y.min() == y.max(): eta[te] += (y.mean() if tr.sum() else 0.5) / reps; continue
                eta[te] += sig(Xd[te] @ ridge_logit(Xd[tr], y, lam=lam)) / reps
    return x - eta
A = []
for design in (["random"] if __import__("os").environ.get("QUICK") == "1" else ["random", "latin"]):
    L, PR = load(design, True)
    for c in C6:
        ids = [i for i in sorted(PG) if gold[(i, c)] is not None and all((m, i, c) in L for m in MODELS)]
        cls = np.array([gold[(i, c)] for i in ids]); base = np.column_stack([np.ones(len(ids)), std(np.array([PG[i][:10] for i in ids]))])
        E = {}
        for m in MODELS:
            pr = [PR[(m, i)] for i in ids]; Xd = np.column_stack([base, dummies(pr)]) if len(set(pr)) > 1 else base
            E[m] = crossfit_resid(Xd, np.array([L[(m, i, c)] for i in ids], float), cls)
        for m1, m2 in itertools.combinations(MODELS, 2):
            if GROUP[m1] == GROUP[m2]: continue
            mi = E[m1] * E[m2]; z = mi.mean() / (mi.std(ddof=1) / np.sqrt(len(mi)))
            A.append({"design": design, "construct": c, "model 1": m1, "model 2": m2, "n": len(ids),
                      "residual corr": mi.mean() / np.sqrt((E[m1] ** 2).mean() * (E[m2] ** 2).mean()), "p": pval(z)})
A = pd.DataFrame(A); print("A done", flush=True)

# ---------------- B: new sample, group LCM ----------------
GR = ["Sonnet", "Gemma", "Qwen-FT", "GPT"]
def group_probs(par, Xm, X, a, groups=GR):
    """Per-unit probability of each group's observed pattern given class a (vectorised over units)."""
    out = []
    for g in groups:
        if g == "GPT":
            pl = sig(Xm["GPT-6 Luna"] @ par[a]["GPT-6 Luna"]); pm = sig(np.column_stack([Xm["GPT-5.4 mini"], X["GPT-6 Luna"]]) @ par[a]["GPT-5.4 mini"])
            out.append(np.where(X["GPT-6 Luna"] == 1, pl, 1 - pl) * np.where(X["GPT-5.4 mini"] == 1, pm, 1 - pm))
        else:
            m = [k for k, v in GROUP.items() if v == g][0]; p = sig(Xm[m] @ par[a][m]); out.append(np.where(X[m] == 1, p, 1 - p))
    return out

def fit(X, Xpi, Xm, groups=GR, lam=2.0, iters=80):
    n = len(Xpi); mods = [m for m in MODELS if GROUP[m] in groups]
    des = {m: (np.column_stack([Xm[m], X["GPT-6 Luna"]]) if m == "GPT-5.4 mini" and "GPT" in groups else Xm[m]) for m in mods}
    g = np.zeros(Xpi.shape[1]); par = {a: {m: np.r_[(1.5 if a else -2.0), np.zeros(des[m].shape[1] - 1)] for m in mods} for a in (0, 1)}
    for _ in range(iters):
        pi = sig(Xpi @ g); l = {}
        for a in (0, 1):
            pr = group_probs(par, Xm, X, a, groups) if "GPT" in groups else \
                 [np.where(X[m] == 1, sig(Xm[m] @ par[a][m]), 1 - sig(Xm[m] @ par[a][m])) for m in mods]
            l[a] = np.prod(pr, 0) * (pi if a else 1 - pi)
        w = l[1] / (l[1] + l[0] + 1e-300)
        g = ridge_logit(np.vstack([Xpi, Xpi]), np.r_[np.ones(n), np.zeros(n)], np.r_[w, 1 - w], lam, g, 8)
        for a, ww in ((1, w), (0, 1 - w)):
            for m in mods: par[a][m] = ridge_logit(des[m], X[m].astype(float), ww, lam, par[a][m], 8)
    pi = sig(Xpi @ g)
    if np.mean([sig(des[m] @ par[1][m]).mean() - sig(des[m] @ par[0][m]).mean() for m in mods]) < 0: pi = 1 - pi; par = {0: par[1], 1: par[0]}
    return pi, par

def cat_probs(par, Xm, a, g):
    """Category probabilities of group g for class a: (n x K) matrix and the observed-category function."""
    if g == "GPT":
        pl = sig(Xm["GPT-6 Luna"] @ par[a]["GPT-6 Luna"])
        pm = [sig(np.column_stack([Xm["GPT-5.4 mini"], np.full(len(pl), u)]) @ par[a]["GPT-5.4 mini"]) for u in (0, 1)]
        return np.column_stack([(1 - pl) * (1 - pm[0]), (1 - pl) * pm[0], pl * (1 - pm[1]), pl * pm[1]])
    m = [k for k, v in GROUP.items() if v == g][0]; p = sig(Xm[m] @ par[a][m]); return np.column_stack([1 - p, p])
def obs_cat(X, g): return 2 * X["GPT-6 Luna"] + X["GPT-5.4 mini"] if g == "GPT" else X[[k for k, v in GROUP.items() if v == g][0]]

def bvr(X, Xm, pi, par):
    tot, per = 0.0, {}
    cp = {a: {g: cat_probs(par, Xm, a, g) for g in GR} for a in (0, 1)}
    for g1, g2 in itertools.combinations(GR, 2):
        st = 0.0; o1, o2 = obs_cat(X, g1), obs_cat(X, g2)
        for u in range(cp[0][g1].shape[1]):
            for v in range(cp[0][g2].shape[1]):
                E = (pi * cp[1][g1][:, u] * cp[1][g2][:, v] + (1 - pi) * cp[0][g1][:, u] * cp[0][g2][:, v]).sum(); Ob = ((o1 == u) & (o2 == v)).sum()
                st += (Ob - E) ** 2 / max(E, 1e-6)
        per[f"{g1} – {g2}"] = st; tot += st
    return tot, per

def simulate(pi, par, Xm):
    n = len(pi); z = rng.random(n) < pi; X = {}
    for m in ["Sonnet 5.5", "Gemma 3 12B", "Qwen3-14B fine-tuned", "GPT-6 Luna"]:
        p = np.where(z, sig(Xm[m] @ par[1][m]), sig(Xm[m] @ par[0][m])); X[m] = (rng.random(n) < p).astype(int)
    pm = np.where(z, sig(np.column_stack([Xm["GPT-5.4 mini"], X["GPT-6 Luna"]]) @ par[1]["GPT-5.4 mini"]),
                  sig(np.column_stack([Xm["GPT-5.4 mini"], X["GPT-6 Luna"]]) @ par[0]["GPT-5.4 mini"]))
    X["GPT-5.4 mini"] = (rng.random(n) < pm).astype(int); return X

import os; QUICK = os.environ.get("QUICK") == "1"
Bo, Bs = [], []; NB_GOF, NB_SUB = (3, 2) if QUICK else (100, 60)
for design in (["random"] if QUICK else ["random", "latin"]):
    L, PR = load(design, False); ids = sorted({k[1] for k in L if k[0] == "Sonnet 5.5"})
    base = np.column_stack([np.ones(len(ids)), std(np.array([PN[i][:5] for i in ids]))])
    Xm = {m: (np.column_stack([base, dummies([PR[(m, i)] for i in ids])]) if m != "Qwen3-14B fine-tuned" else base) for m in MODELS}
    for c in C6:
        t0 = time.time(); X = {m: np.array([L[(m, i, c)] for i in ids]) for m in MODELS}
        pi, par = fit(X, base, Xm); T, per = bvr(X, Xm, pi, par); Tb = []
        for _ in range(NB_GOF):
            Xb = simulate(pi, par, Xm); pb, parb = fit(Xb, base, Xm, iters=40); Tb.append(bvr(Xb, Xm, pb, parb)[0])
        wst = max(per, key=per.get)
        Bo.append({"design": design, "construct": c, "prevalence": pi.mean(), "BVR total": T, "bootstrap p": (np.sum(np.array(Tb) >= T) + 1) / (NB_GOF + 1),
                   "worst group pair": wst, "worst pair BVR": per[wst], **{f"BVR {k}": v for k, v in per.items()}})
        subs = list(itertools.combinations(GR, 3)); est = np.array([fit(X, base, Xm, groups=s)[0].mean() for s in subs]); boot = []
        for _ in range(NB_SUB):
            ix = rng.integers(0, len(ids), len(ids)); Xi = {m: v[ix] for m, v in X.items()}; Xmi = {m: v[ix] for m, v in Xm.items()}
            boot.append([fit(Xi, base[ix], Xmi, groups=s, iters=40)[0].mean() for s in subs])
        boot = np.array(boot); dv = boot - est; Th = ((est - est.mean()) ** 2).sum(); Thb = ((dv - dv.mean(1, keepdims=True)) ** 2).sum(1)
        Bs.append({"design": design, "construct": c, "min subset prevalence": est.min(), "max subset prevalence": est.max(),
                   "heterogeneity p": (np.sum(Thb >= Th) + 1) / (NB_SUB + 1), **{" + ".join(s): e for s, e in zip(subs, est)}})
        print(design, c, f"{time.time() - t0:.0f}s", flush=True)
Bo, Bs = pd.DataFrame(Bo), pd.DataFrame(Bs)
with pd.ExcelWriter(D0 / ("CI_latin_QUICKTEST.xlsx" if QUICK else "CI_latin_results.xlsx")) as w:
    A.to_excel(w, sheet_name="A gold between-group", index=False); Bo.to_excel(w, sheet_name="B overidentification", index=False)
    Bs.to_excel(w, sheet_name="B subset prevalence", index=False)
json.dump({"A": A.to_dict("records"), "Bo": Bo.to_dict("records"), "Bs": Bs.to_dict("records")}, open(O / "ci_latin.json", "w"), indent=1, default=float)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print("== A gold, between-group pairs (9): median residual corr / #p<.05")
print(A.groupby(["construct", "design"]).agg(med=("residual corr", "median"), sig=("p", lambda p: int((p < .05).sum())), n=("p", "size")).unstack("design").round(2).to_string())
print("== B overidentification"); print(Bo[["design", "construct", "prevalence", "BVR total", "bootstrap p", "worst group pair", "worst pair BVR"]].round(3).to_string(index=False))
print("== B subset"); print(Bs[["design", "construct", "min subset prevalence", "max subset prevalence", "heterogeneity p"]].round(3).to_string(index=False))
