"""Add the prompt version to the conditioning set D (Egami & Shin 2026, Assumption 3.1: annotation-level information).
Prompt is model-specific: each model's error rates may depend on ITS OWN prompt; P(X*=1|D) does not (prompts were randomised).
A. Gold sample (100): cross-fitted residual moments with D = embedding PCs (+ own-prompt dummies for Luna / 5.4 mini, the only
   models with randomised prompts on the gold sample). Also a direct check: Luna-5.4 mini residual correlation when the two
   used the SAME prompt vs DIFFERENT prompts.
B. New sample (150): latent class model with covariates, model-specific prompt dummies in each model's error model;
   bivariate-residual overidentification test (parametric bootstrap) and subset prevalence heterogeneity.
Writes CI_prompt_results.xlsx."""
import json, itertools, time, csv
from math import erf, sqrt
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.decomposition import PCA
D0 = Path(__file__).resolve().parent.parent; F = D0.parent / "11.16_humanAIcomparasion_finetune"
C6 = ["Absence of Naive Realism", "Theme", "Thought-Provoking", "Ease", "Critic", "Surprise"]
rng = np.random.default_rng(2026)
Z = np.load(D0 / "outputs" / "embeddings.npz")
pca = PCA(40, random_state=0).fit(np.vstack([Z["E_gold"], Z["E_new"]]))
PG = {int(i): r for i, r in zip(Z["ids_gold"], pca.transform(Z["E_gold"]))}
PN = {int(i): r for i, r in zip(Z["ids_new"], pca.transform(Z["E_new"]))}
sig = lambda v: 1 / (1 + np.exp(-np.clip(v, -30, 30)))
pval = lambda z: 2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2))))

def ridge_logit(X, y, w=None, lam=1.0, beta=None, iters=25):
    n, p = X.shape; w = np.ones(n) if w is None else w; b = np.zeros(p) if beta is None else beta.copy()
    P = lam * np.eye(p); P[0, 0] = 0
    for _ in range(iters):
        mu = sig(X @ b); s = w * mu * (1 - mu) + 1e-9
        step = np.linalg.solve(X.T @ (X * s[:, None]) + P, X.T @ (w * (y - mu)) - P @ b); b += step
        if np.abs(step).max() < 1e-6: break
    return b

def std(P): return (P - P.mean(0)) / P.std(0)
def dummies(pr): return np.column_stack([np.array(pr) == "v3", np.array(pr) == "v4"]).astype(float)

# ---------------- A ----------------
ds = json.load(open(F / "data" / "dataset.json", encoding="utf-8"))
gold = {(it["review_id"], c): it["labels"][c] for it in ds["items"] for c in C6}
G = {}
for name, k in [("GPT-4o", "gpt4o"), ("Sonnet 5.5", "sonnet"), ("Qwen3-14B Ollama", "qwen"), ("Gemma 3 12B", "gemma")]:
    for r in map(json.loads, open(F / "data" / f"exp3_labels_{k}.jsonl", encoding="utf-8")):
        if r["label"] is not None: G[(name, r["review_id"] + 1, r["construct"])] = int(r["label"])
for r in map(json.loads, open(F / "outputs" / "predictions_finetuned.jsonl", encoding="utf-8")):
    G[("Qwen3-14B fine-tuned", r["review_id"], r["construct"])] = int(r["pred"])
GP = {}
for name, k in [("GPT-6 Luna", "luna"), ("GPT-5.4 mini", "mini")]:
    for r in map(json.loads, open(D0 / "outputs" / f"gold_progress_{k}.jsonl", encoding="utf-8")):
        if r["label"] is not None: G[(name, r["sample_id"], r["construct"])] = int(r["label"])
    GP[name] = {int(r["sample_id"]): r["prompt"] for r in csv.DictReader(open(D0 / "outputs" / f"gold_prompt_assignment_{k}.csv"))}
GM = ["GPT-4o", "Sonnet 5.5", "Qwen3-14B Ollama", "Gemma 3 12B", "Qwen3-14B fine-tuned", "GPT-6 Luna", "GPT-5.4 mini"]
S5 = ["Sonnet 5.5", "Gemma 3 12B", "Qwen3-14B fine-tuned", "GPT-6 Luna", "GPT-5.4 mini"]

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

A, SAME = [], []
for c in C6:
    ids = [i for i in sorted(PG) if gold[(i, c)] is not None and all((m, i, c) in G for m in GM)]
    cls = np.array([gold[(i, c)] for i in ids]); E10 = std(np.array([PG[i][:10] for i in ids]))
    for spec in ["pc=10", "pc=10 + prompt"]:
        E = {}
        for m in GM:
            Xd = np.column_stack([np.ones(len(ids)), E10])
            if spec.endswith("prompt") and m in GP: Xd = np.column_stack([Xd, dummies([GP[m][i] for i in ids])])
            E[m] = crossfit_resid(Xd, np.array([G[(m, i, c)] for i in ids], float), cls)
        for m1, m2 in itertools.combinations(GM, 2):
            mi = E[m1] * E[m2]; z = mi.mean() / (mi.std(ddof=1) / np.sqrt(len(mi)))
            A.append({"construct": c, "D": spec, "model 1": m1, "model 2": m2, "residual corr": mi.mean() / np.sqrt((E[m1] ** 2).mean() * (E[m2] ** 2).mean()),
                      "p": pval(z), "both Stage-3": m1 in S5 and m2 in S5, "involves Luna/mini": m1 in GP or m2 in GP})
        if spec == "pc=10":   # same vs different prompt, Luna vs 5.4 mini, residuals given embeddings
            same = np.array([GP["GPT-6 Luna"][i] == GP["GPT-5.4 mini"][i] for i in ids]); e1, e2 = E["GPT-6 Luna"], E["GPT-5.4 mini"]
            for lab, idx in (("same prompt", same), ("different prompt", ~same)):
                SAME.append({"construct": c, "group": lab, "n": int(idx.sum()),
                             "residual corr": (e1[idx] * e2[idx]).mean() / np.sqrt((e1[idx] ** 2).mean() * (e2[idx] ** 2).mean())})
            # with v2-fixed models: Luna/mini residual corr with Sonnet/Gemma/GPT-4o/Qwen-Ollama when Luna/mini also used v2 vs not
            for m in ("GPT-6 Luna", "GPT-5.4 mini"):
                v2 = np.array([GP[m][i] == "v2" for i in ids])
                for lab, idx in (("also v2", v2), ("v3/v4", ~v2)):
                    rr = [(E[m][idx] * E[o][idx]).mean() / np.sqrt((E[m][idx] ** 2).mean() * (E[o][idx] ** 2).mean()) for o in ["GPT-4o", "Sonnet 5.5", "Qwen3-14B Ollama", "Gemma 3 12B"]]
                    SAME.append({"construct": c, "group": f"{m} vs v2-fixed models: {lab}", "n": int(idx.sum()), "residual corr": float(np.mean(rr))})
A, SAME = pd.DataFrame(A), pd.DataFrame(SAME)
print("A done", flush=True)

# ---------------- B ----------------
NM = {"sonnet": "Sonnet 5.5", "gemma": "Gemma 3 12B", "qwenft": "Qwen3-14B fine-tuned", "luna": "GPT-6 Luna", "mini": "GPT-5.4 mini"}
L, PR = {}, {}
for k, n in NM.items():
    for r in map(json.loads, open(D0 / "outputs" / f"progress_{k}.jsonl", encoding="utf-8")):
        if k == "qwenft": L[(n, r["review_id"], r["construct"])] = int(r["pred"]); PR[(n, r["review_id"])] = "v1"
        elif r["label"] is not None: L[(n, r["sample_id"], r["construct"])] = int(r["label"]); PR[(n, r["sample_id"])] = r["prompt"]
M5 = list(NM.values()); ids150 = sorted({k[1] for k in L})

def lcm(X, Xpi, Xm, lam=2.0, iters=80):
    """Xpi: design for P(X*=1|D); Xm: list of per-model designs for the error model."""
    n, J = X.shape; g = np.zeros(Xpi.shape[1]); g[0] = np.log(X.mean() / (1 - X.mean()) + 1e-9)
    b1 = [np.r_[1.5, np.zeros(Xm[j].shape[1] - 1)] for j in range(J)]; b0 = [np.r_[-2.0, np.zeros(Xm[j].shape[1] - 1)] for j in range(J)]
    for _ in range(iters):
        pi = sig(Xpi @ g); s1 = np.column_stack([sig(Xm[j] @ b1[j]) for j in range(J)]); s0 = np.column_stack([sig(Xm[j] @ b0[j]) for j in range(J)])
        l1 = pi * np.prod(np.where(X == 1, s1, 1 - s1), 1); l0 = (1 - pi) * np.prod(np.where(X == 1, s0, 1 - s0), 1); w = l1 / (l1 + l0 + 1e-300)
        g = ridge_logit(np.vstack([Xpi, Xpi]), np.r_[np.ones(n), np.zeros(n)], np.r_[w, 1 - w], lam, g, 8)
        for j in range(J):
            b1[j] = ridge_logit(Xm[j], X[:, j].astype(float), w, lam, b1[j], 8); b0[j] = ridge_logit(Xm[j], X[:, j].astype(float), 1 - w, lam, b0[j], 8)
    pi = sig(Xpi @ g); s1 = np.column_stack([sig(Xm[j] @ b1[j]) for j in range(J)]); s0 = np.column_stack([sig(Xm[j] @ b0[j]) for j in range(J)])
    if np.mean(s1 - s0) < 0: pi, s1, s0 = 1 - pi, s0, s1
    return pi, s1, s0

def bvr(X, pi, s1, s0):
    tot, per = 0.0, {}
    for j, k in itertools.combinations(range(X.shape[1]), 2):
        st = 0.0
        for u, v in itertools.product((0, 1), repeat=2):
            a1 = s1[:, j] if u else 1 - s1[:, j]; c1 = s1[:, k] if v else 1 - s1[:, k]; a0 = s0[:, j] if u else 1 - s0[:, j]; c0 = s0[:, k] if v else 1 - s0[:, k]
            E = (pi * a1 * c1 + (1 - pi) * a0 * c0).sum(); O = ((X[:, j] == u) & (X[:, k] == v)).sum(); st += (O - E) ** 2 / max(E, 1e-6)
        per[(j, k)] = st; tot += st
    return tot, per

def designs(ix, k, prompt):
    base = np.ones((len(ix), 1)) if k == 0 else np.column_stack([np.ones(len(ix)), std(np.array([PN[i][:k] for i in ix]))])
    Xm = [np.column_stack([base, dummies([PR[(m, i)] for i in ix])]) if (prompt and m != "Qwen3-14B fine-tuned") else base for m in M5]
    return base, Xm

trip = list(itertools.combinations(range(5), 3)); NB_GOF, NB_SUB = 100, 60
Bo, Bs = [], []
for c in C6:
    X = np.array([[L[(m, i, c)] for m in M5] for i in ids150]); idx_all = np.arange(len(ids150))
    for k, prompt, lab in [(0, True, "prompt only"), (5, True, "pc=5 + prompt")]:
        t0 = time.time(); Xpi, Xm = designs(ids150, k, prompt)
        pi, s1, s0 = lcm(X, Xpi, Xm); T, per = bvr(X, pi, s1, s0); Tb = []
        for _ in range(NB_GOF):
            z = rng.random(len(X)) < pi; Xb = np.where(z[:, None], rng.random(X.shape) < s1, rng.random(X.shape) < s0).astype(int)
            Tb.append(bvr(Xb, *lcm(Xb, Xpi, Xm, iters=40))[0])
        wst = max(per, key=per.get)
        Bo.append({"construct": c, "D": lab, "prevalence": pi.mean(), "BVR total": T, "bootstrap p": (np.sum(np.array(Tb) >= T) + 1) / (NB_GOF + 1),
                   "worst pair": f"{M5[wst[0]]} – {M5[wst[1]]}", "worst pair BVR": per[wst]})
        est = np.array([lcm(X[:, list(t)], Xpi, [Xm[j] for j in t])[0].mean() for t in trip]); boot = []
        for _ in range(NB_SUB):
            ix = rng.integers(0, len(X), len(X))
            boot.append([lcm(X[ix][:, list(t)], Xpi[ix], [Xm[j][ix] for j in t], iters=40)[0].mean() for t in trip])
        boot = np.array(boot); dv = boot - est; Th = ((est - est.mean()) ** 2).sum(); Thb = ((dv - dv.mean(1, keepdims=True)) ** 2).sum(1)
        Bs.append({"construct": c, "D": lab, "min subset prevalence": est.min(), "max subset prevalence": est.max(), "heterogeneity p": (np.sum(Thb >= Th) + 1) / (NB_SUB + 1)})
        print(c, lab, f"{time.time() - t0:.0f}s", flush=True)
Bo, Bs = pd.DataFrame(Bo), pd.DataFrame(Bs)
with pd.ExcelWriter(D0 / "CI_prompt_results.xlsx") as w:
    A.to_excel(w, sheet_name="A gold residual moments", index=False); SAME.to_excel(w, sheet_name="A same vs different prompt", index=False)
    Bo.to_excel(w, sheet_name="B overidentification", index=False); Bs.to_excel(w, sheet_name="B subset prevalence", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print("== A: pairs involving Luna/5.4 mini, median residual corr and #p<.05")
print(A[A["involves Luna/mini"]].groupby(["construct", "D"]).agg(med=("residual corr", "median"), sig=("p", lambda p: int((p < .05).sum())), n=("p", "size")).unstack("D").round(2).to_string())
print("== A: 5 Stage-3 models"); print(A[A["both Stage-3"]].groupby(["construct", "D"]).agg(med=("residual corr", "median"), sig=("p", lambda p: int((p < .05).sum()))).unstack("D").round(2).to_string())
print("== same vs different prompt"); print(SAME.pivot(index="construct", columns="group", values="residual corr").round(2).to_string())
print(SAME.groupby("group")["n"].first().to_string())
print("== B"); print(Bo.round(3).to_string(index=False)); print(Bs.round(3).to_string(index=False))
