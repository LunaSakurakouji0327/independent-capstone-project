"""CI diagnostics conditioning on OpenAI text embeddings (Egami & Shin 2026, Assumption 3.1 with D = embedding).
Embeddings (text-embedding-3-large, 3072-d) are reduced by PCA fitted on all 250 texts (unsupervised); D = first k PCs.

A. Gold sample (100 reviews, 7 models), Sec. 5.3 with continuous D: cross-fitted residual interaction moments.
   eta_{j,a}(D) = P(X_j = 1 | X* = a, D) by ridge logistic regression, 5-fold cross-fitting (repeated 5x, averaged).
   e_ij = X_ij - eta_hat; moment m_i = e_ij * e_ik (each unit uses its own true class); z-test of E[m] = 0.
   Compared across D = none, length tertile, embedding PCs (k = 5, 10, 20).
B. New sample (150 reviews, 5 models), Sec. 5.2: latent class model with covariates
   P(X*=1|D) = logit^-1(g'D),  P(X_j=1|X*=a,D) = logit^-1(a_ja + b_ja'D), fitted by EM with ridge-penalised IRLS.
   (i) Bivariate-residual overidentification test: observed vs model-implied joint frequencies for every model pair,
       sum over pairs and cells of (O-E)^2/E, parametric bootstrap p-value.
   (ii) Subset diagnostic: mean prevalence from each 3-model subset, centered nonparametric bootstrap heterogeneity test.
   Compared across D = none and embedding PCs (k = 3, 5).
Writes CI_embedding_results.xlsx and outputs/ci_embed.json."""
import json, itertools, time
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.decomposition import PCA
D0 = Path(__file__).resolve().parent.parent; F = D0.parent / "11.16_humanAIcomparasion_finetune"
C6 = ["Absence of Naive Realism", "Theme", "Thought-Provoking", "Ease", "Critic", "Surprise"]
rng = np.random.default_rng(2026)
Z = np.load(D0 / "outputs" / "embeddings.npz")
pca = PCA(40, random_state=0).fit(np.vstack([Z["E_gold"], Z["E_new"]]))
def pcs(E, k):
    P = pca.transform(E)[:, :k]; return (P - P.mean(0)) / P.std(0)
PG = {int(i): r for i, r in zip(Z["ids_gold"], pca.transform(Z["E_gold"]))}
PN = {int(i): r for i, r in zip(Z["ids_new"], pca.transform(Z["E_new"]))}

def ridge_logit(X, y, w=None, lam=1.0, beta=None, iters=25):
    """Weighted ridge logistic regression by IRLS; X includes an intercept column (not penalised)."""
    n, p = X.shape; w = np.ones(n) if w is None else w; b = np.zeros(p) if beta is None else beta.copy()
    P = lam * np.eye(p); P[0, 0] = 0
    for _ in range(iters):
        mu = 1 / (1 + np.exp(-np.clip(X @ b, -30, 30))); s = w * mu * (1 - mu) + 1e-9
        g = X.T @ (w * (y - mu)) - P @ b; H = X.T @ (X * s[:, None]) + P
        step = np.linalg.solve(H, g); b += step
        if np.abs(step).max() < 1e-6: break
    return b

# ---------------- A: gold sample ----------------
ds = json.load(open(F / "data" / "dataset.json", encoding="utf-8"))
gold = {(it["review_id"], c): it["labels"][c] for it in ds["items"] for c in C6}
wl = {it["review_id"]: len(it["text"].split()) for it in ds["items"]}; cuts = np.quantile(list(wl.values()), [1 / 3, 2 / 3])
G = {}
for name, k in [("GPT-4o", "gpt4o"), ("Sonnet 5.5", "sonnet"), ("Qwen3-14B Ollama", "qwen"), ("Gemma 3 12B", "gemma")]:
    for r in map(json.loads, open(F / "data" / f"exp3_labels_{k}.jsonl", encoding="utf-8")):
        if r["label"] is not None: G[(name, r["review_id"] + 1, r["construct"])] = int(r["label"])
for r in map(json.loads, open(F / "outputs" / "predictions_finetuned.jsonl", encoding="utf-8")):
    G[("Qwen3-14B fine-tuned", r["review_id"], r["construct"])] = int(r["pred"])
for name, k in [("GPT-6 Luna", "luna"), ("GPT-5.4 mini", "mini")]:
    for r in map(json.loads, open(D0 / "outputs" / f"gold_progress_{k}.jsonl", encoding="utf-8")):
        if r["label"] is not None: G[(name, r["sample_id"], r["construct"])] = int(r["label"])
GM = ["GPT-4o", "Sonnet 5.5", "Qwen3-14B Ollama", "Gemma 3 12B", "Qwen3-14B fine-tuned", "GPT-6 Luna", "GPT-5.4 mini"]
S5 = ["Sonnet 5.5", "Gemma 3 12B", "Qwen3-14B fine-tuned", "GPT-6 Luna", "GPT-5.4 mini"]

def design(ids, spec):
    if spec == "none": return np.ones((len(ids), 1))
    if spec == "length": t = np.array([np.searchsorted(cuts, wl[i], side="right") for i in ids]); return np.column_stack([np.ones(len(ids)), t == 1, t == 2]).astype(float)
    k = int(spec.split("=")[1]); P = np.array([PG[i][:k] for i in ids]); P = (P - P.mean(0)) / P.std(0)
    return np.column_stack([np.ones(len(ids)), P])

def crossfit_eta(Xd, x, cls, lam, reps=5):
    eta = np.zeros(len(x))
    for r in range(reps):
        fold = np.random.default_rng(100 + r).permutation(len(x)) % 5
        for f in range(5):
            for a in (0, 1):
                tr = (fold != f) & (cls == a); te = (fold == f) & (cls == a)
                if te.sum() == 0: continue
                y = x[tr]
                if tr.sum() < 3 or y.min() == y.max(): eta[te] += (y.mean() if tr.sum() else 0.5) / reps; continue
                b = ridge_logit(Xd[tr], y, lam=lam); eta[te] += 1 / (1 + np.exp(-Xd[te] @ b)) / reps
    return eta

SPECS = ["none", "length", "pc=5", "pc=10", "pc=20"]
A = []
for c in C6:
    for spec in SPECS:
        ids = [i for i in sorted(wl) if gold[(i, c)] is not None and all((m, i, c) in G for m in GM)]
        cls = np.array([gold[(i, c)] for i in ids]); Xd = design(ids, spec)
        E = {m: (lambda x: x - crossfit_eta(Xd, x, cls, lam=2.0))(np.array([G[(m, i, c)] for i in ids], float)) for m in GM}
        for m1, m2 in itertools.combinations(GM, 2):
            mi = E[m1] * E[m2]; den = np.sqrt((E[m1] ** 2).mean() * (E[m2] ** 2).mean())
            z = mi.mean() / (mi.std(ddof=1) / np.sqrt(len(mi))) if mi.std() > 0 else np.nan
            from math import erf, sqrt
            p = 2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2)))) if z == z else np.nan
            A.append({"construct": c, "D": spec, "model 1": m1, "model 2": m2, "n": len(ids), "residual corr": mi.mean() / den if den > 0 else np.nan,
                      "z": z, "p": p, "both Stage-3 models": m1 in S5 and m2 in S5})
A = pd.DataFrame(A)
A["q (BH, construct x D)"] = np.nan
for (c, s), d in A.groupby(["construct", "D"]):
    d = d[d.p.notna()]; o = np.argsort(d.p.values); m = len(o)
    q = np.minimum.accumulate((d.p.values[o] * m / np.arange(1, m + 1))[::-1])[::-1]; A.loc[d.index[o], "q (BH, construct x D)"] = np.minimum(q, 1)
print("A done", flush=True)

# ---------------- B: new sample, latent class model with embedding covariates ----------------
NM = {"sonnet": "Sonnet 5.5", "gemma": "Gemma 3 12B", "qwenft": "Qwen3-14B fine-tuned", "luna": "GPT-6 Luna", "mini": "GPT-5.4 mini"}
L = {}
for k, n in NM.items():
    for r in map(json.loads, open(D0 / "outputs" / f"progress_{k}.jsonl", encoding="utf-8")):
        if k == "qwenft": L[(n, r["review_id"], r["construct"])] = int(r["pred"])
        elif r["label"] is not None: L[(n, r["sample_id"], r["construct"])] = int(r["label"])
ids150 = sorted({k[1] for k in L})

def lcm(X, Xd, lam=2.0, iters=80):
    n, J = X.shape; p = Xd.shape[1]
    g = np.zeros(p); g[0] = np.log(X.mean() / (1 - X.mean() + 1e-9) + 1e-9)
    b1 = np.tile(np.r_[1.5, np.zeros(p - 1)], (J, 1)); b0 = np.tile(np.r_[-2.0, np.zeros(p - 1)], (J, 1))
    sig = lambda v: 1 / (1 + np.exp(-np.clip(v, -30, 30)))
    for _ in range(iters):
        pi = sig(Xd @ g); s1 = sig(Xd @ b1.T); s0 = sig(Xd @ b0.T)
        l1 = pi * np.prod(np.where(X == 1, s1, 1 - s1), 1); l0 = (1 - pi) * np.prod(np.where(X == 1, s0, 1 - s0), 1)
        w = l1 / (l1 + l0 + 1e-300)
        Xs = np.vstack([Xd, Xd]); g = ridge_logit(Xs, np.r_[np.ones(n), np.zeros(n)], np.r_[w, 1 - w], lam, g, 8)
        for j in range(J):
            b1[j] = ridge_logit(Xd, X[:, j].astype(float), w, lam, b1[j], 8); b0[j] = ridge_logit(Xd, X[:, j].astype(float), 1 - w, lam, b0[j], 8)
    pi = sig(Xd @ g); s1 = sig(Xd @ b1.T); s0 = sig(Xd @ b0.T)
    if np.mean(s1 - s0) < 0: pi, s1, s0 = 1 - pi, s0, s1
    return pi, s1, s0

def bvr(X, pi, s1, s0):
    J = X.shape[1]; tot = 0.0; per = {}
    for j, k in itertools.combinations(range(J), 2):
        st = 0.0
        for u, v in itertools.product((0, 1), repeat=2):
            pj1 = s1[:, j] if u else 1 - s1[:, j]; pk1 = s1[:, k] if v else 1 - s1[:, k]
            pj0 = s0[:, j] if u else 1 - s0[:, j]; pk0 = s0[:, k] if v else 1 - s0[:, k]
            E = (pi * pj1 * pk1 + (1 - pi) * pj0 * pk0).sum(); O = ((X[:, j] == u) & (X[:, k] == v)).sum()
            st += (O - E) ** 2 / max(E, 1e-6)
        per[(j, k)] = st; tot += st
    return tot, per

def dmat(spec):
    if spec == "none": return np.ones((len(ids150), 1))
    k = int(spec.split("=")[1]); P = np.array([PN[i][:k] for i in ids150]); P = (P - P.mean(0)) / P.std(0)
    return np.column_stack([np.ones(len(ids150)), P])

M5 = list(NM.values()); trip = list(itertools.combinations(range(5), 3)); NB_GOF, NB_SUB = 100, 60
Bo, Bs = [], []
for c in C6:
    X = np.array([[L[(m, i, c)] for m in M5] for i in ids150])
    for spec in ["none", "pc=3", "pc=5"]:
        t0 = time.time(); Xd = dmat(spec)
        pi, s1, s0 = lcm(X, Xd); T, per = bvr(X, pi, s1, s0); Tb = []
        for _ in range(NB_GOF):
            z = rng.random(len(X)) < pi
            Xb = np.where(z[:, None], rng.random(X.shape) < s1, rng.random(X.shape) < s0).astype(int)
            Tb.append(bvr(Xb, *lcm(Xb, Xd, iters=40))[0])
        worst = max(per, key=per.get)
        Bo.append({"construct": c, "D": spec, "prevalence": pi.mean(), "BVR total": T, "bootstrap p": (np.sum(np.array(Tb) >= T) + 1) / (NB_GOF + 1),
                   "worst pair": f"{M5[worst[0]]} – {M5[worst[1]]}", "worst pair BVR": per[worst]})
        est = np.array([lcm(X[:, list(t)], Xd)[0].mean() for t in trip]); boot = []
        for _ in range(NB_SUB):
            ix = rng.integers(0, len(X), len(X)); boot.append([lcm(X[ix][:, list(t)], Xd[ix], iters=40)[0].mean() for t in trip])
        boot = np.array(boot); dv = boot - est; Th = ((est - est.mean()) ** 2).sum(); Thb = ((dv - dv.mean(1, keepdims=True)) ** 2).sum(1)
        Bs.append({"construct": c, "D": spec, "min subset prevalence": est.min(), "max subset prevalence": est.max(),
                   "heterogeneity p": (np.sum(Thb >= Th) + 1) / (NB_SUB + 1), **{" + ".join(M5[j] for j in t): e for t, e in zip(trip, est)}})
        print(c, spec, f"{time.time() - t0:.0f}s", flush=True)
Bo, Bs = pd.DataFrame(Bo), pd.DataFrame(Bs)

ev = pca.explained_variance_ratio_
with pd.ExcelWriter(D0 / "CI_embedding_results.xlsx") as w:
    A.to_excel(w, sheet_name="A gold residual moments", index=False)
    Bo.to_excel(w, sheet_name="B overidentification (BVR)", index=False); Bs.to_excel(w, sheet_name="B subset prevalence", index=False)
    pd.DataFrame({"PC": range(1, 41), "explained variance": ev, "cumulative": ev.cumsum()}).to_excel(w, sheet_name="PCA", index=False)
json.dump({"A": A.to_dict("records"), "Bo": Bo.to_dict("records"), "Bs": Bs.to_dict("records"), "pca_cum": ev.cumsum().tolist()},
          open(D0 / "outputs" / "ci_embed.json", "w"), indent=1, default=float)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print("PCA cumulative variance k=5,10,20:", ev.cumsum()[[4, 9, 19]].round(3))
for sub, lab in [(A, "all 7 models, 21 pairs"), (A[A["both Stage-3 models"]], "5 Stage-3 models, 10 pairs")]:
    print(f"== A ({lab}): median residual corr / pairs with p<.05")
    t = sub.groupby(["construct", "D"]).agg(med=("residual corr", "median"), sig=("p", lambda p: int((p < .05).sum())), qsig=("q (BH, construct x D)", lambda q: int((q < .10).sum())))
    print(t.unstack("D").round(2).to_string())
print("== B overidentification"); print(Bo.round(3).to_string(index=False))
print("== B subset"); print(Bs[["construct", "D", "min subset prevalence", "max subset prevalence", "heterogeneity p"]].round(3).to_string(index=False))
