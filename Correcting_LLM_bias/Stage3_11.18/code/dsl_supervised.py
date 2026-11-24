"""DSL (Egami et al. 2023) with a cross-fitted supervised predictor of the human code, compared with gold-only, DSL with
majority-vote imputation, and DMM-DSL (dmm_dsl.py). No conditional-independence assumption is needed for DSL.
Predictor g(X~, D) of X* for each construct: penalised logistic regression trained on the 100 human-coded reviews.
  features "labels only": labels of Gemma, Qwen-FT (label + P(1)), GPT-6 Luna, GPT-5.4 mini, and the share of models coding 1;
  features "labels + text": the above + 5 embedding PCs + log length + genre shares.
Cross-fitting: all 3,000 reviews split into 5 folds; predictions for fold k come from a model trained on the human-coded reviews
outside fold k; the ridge penalty is chosen by 4-fold CV inside the training folds only.
DSL moment: psi = psi(g) + R/rho * (psi(X*) - psi(g)), rho = share of human-coded reviews (100 / 3,000).
Targets as in dmm_dsl.py: prevalence; rating ~ X* + log length + genre shares (rating > 0). Sandwich standard errors.
Writes Stage3/Stage3_DSL_results.xlsx and outputs/dsl_supervised.json."""
import json, itertools
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.decomposition import PCA
from sklearn.metrics import roc_auc_score, log_loss
B = Path(r"C:\Users\gujia\Downloads\books"); S3 = B / "Stage3_11.18"; O = S3 / "outputs"; S2 = B / "Stage2_11.16" / "11.17_5modelcomparasion"
F = B / "Stage2_11.16" / "11.16_humanAIcomparasion_finetune"
C6 = ["Absence of Naive Realism", "Theme", "Thought-Provoking", "Ease", "Critic", "Surprise"]
sig = lambda v: 1 / (1 + np.exp(-np.clip(v, -30, 30)))
U = pd.read_csv(S3 / "data" / "stage3_reviews.csv", encoding="utf-8-sig").set_index("unit_id")
gold_items = {it["review_id"]: it["labels"] for it in json.load(open(F / "data" / "dataset.json", encoding="utf-8"))["items"]}
GOLD = {(f"G{r}", c): v for r, l in gold_items.items() for c, v in l.items()}
lab, p1 = {}, {}
def add(key, f, idcol, pref=""):
    if not Path(f).exists(): return
    for r in map(json.loads, open(f, encoding="utf-8")):
        if r.get("label") is None: continue
        lab[(key, pref + str(r[idcol]), r["construct"])] = int(r["label"])
        if "p1" in r: p1[(key, pref + str(r[idcol]), r["construct"])] = r["p1"]
for k in ["gemma", "luna", "mini"]:
    add(k, S2 / "outputs" / f"gold_latin_progress_{k}.jsonl", "sample_id", "G"); add(k, O / f"goldfill_{k}.jsonl", "unit_id"); add(k, O / f"progress_{k}.jsonl", "unit_id")
add("qwenft", O / "progress_qwenft.jsonl", "unit_id")
MODELS = ["gemma", "qwenft", "luna", "mini"]
units = list(U.index); n = len(units)
Z = np.load(O / "embeddings_s3.npz"); emb = dict(zip(Z["unit_id"], Z["E"]))
pcs = PCA(5, random_state=0).fit_transform(np.array([emb[u] for u in units]))
gcols = [c for c in U.columns if c.startswith("genre: ") and c != "genre: top"]
TEXT = np.column_stack([pcs, np.log(U.loc[units, "n_words"].values), U.loc[units, gcols].values])
y_all = U.loc[units, "rating"].values.astype(float)
W = np.column_stack([np.log(U.loc[units, "n_words"].values), U.loc[units, gcols].values[:, 1:]])
fold = np.random.default_rng(11).permutation(n) % 5

def ridge_logit(X, y, lam, iters=50):
    b = np.zeros(X.shape[1]); P = lam * np.eye(X.shape[1]); P[0, 0] = 0
    for _ in range(iters):
        mu = sig(X @ b); s = mu * (1 - mu) + 1e-9
        step = np.linalg.solve(X.T @ (X * s[:, None]) + P, X.T @ (y - mu) - P @ b); b += step
        if np.abs(step).max() < 1e-7: break
    return b
def standardise(A, ref):
    m, s = ref.mean(0), ref.std(0); s[s == 0] = 1; return (A - m) / s
LAMS = [0.3, 1, 3, 10, 30, 100]
def fit_predict(Xtr, ytr, Xte):
    """Choose ridge penalty by 4-fold CV log-loss inside the training data, then fit and predict."""
    inner = np.arange(len(ytr)) % 4; best, bl = None, np.inf
    for lam in LAMS:
        ll = []
        for f in range(4):
            tr, te = inner != f, inner == f
            if ytr[tr].min() == ytr[tr].max(): ll.append(0.0); continue
            Xs = standardise(Xtr, Xtr[tr]); b = ridge_logit(np.column_stack([np.ones(tr.sum()), Xs[tr]]), ytr[tr], lam)
            pr = np.clip(sig(np.column_stack([np.ones(te.sum()), Xs[te]]) @ b), 1e-4, 1 - 1e-4)
            ll.append(-np.mean(ytr[te] * np.log(pr) + (1 - ytr[te]) * np.log(1 - pr)))
        if np.mean(ll) < bl: bl, best = np.mean(ll), lam
    b = ridge_logit(np.column_stack([np.ones(len(ytr)), standardise(Xtr, Xtr)]), ytr, best)
    return sig(np.column_stack([np.ones(len(Xte)), standardise(Xte, Xtr)]) @ b), best

def solve_lin(terms, idx):
    A = 0; bv = 0; ni = idx.sum()
    mk = lambda xv: np.column_stack([np.ones(ni), np.full(ni, xv) if np.isscalar(xv) else xv, W[idx]])
    for wt, xv in terms:
        Zt = mk(xv); A = A + (Zt * wt[:, None]).T @ Zt / ni; bv = bv + (Zt * wt[:, None]).T @ y_all[idx] / ni
    beta = np.linalg.solve(A, bv); psi = 0
    for wt, xv in terms:
        Zt = mk(xv); psi = psi + Zt * (wt * (y_all[idx] - Zt @ beta))[:, None]
    Ai = np.linalg.inv(A); return beta[1], np.sqrt(np.diag(Ai @ np.cov(psi.T) @ Ai.T) / ni)[1]

def dsl(g, R, xg, rho):
    """Prevalence and rating coefficient with imputation g in [0,1] (or any real imputation)."""
    ps = g + R / rho * (xg - g); rr = y_all > 0
    reg = solve_lin([(1 - g[rr], 0.0), (g[rr], 1.0), (R[rr] / rho, xg[rr]), (-(R[rr] / rho) * (1 - g[rr]), 0.0), (-(R[rr] / rho) * g[rr], 1.0)], rr)
    return ps.mean(), ps.std(ddof=1) / np.sqrt(n), reg[0], reg[1]

dmm = {(r["construct"], r["estimator"]): r for r in json.load(open(O / "dmm_dsl_Gemma-Qwen-FT-GPT.json"))["estimates"]}
RES, PRED = [], []
for c in C6:
    L = np.column_stack([[lab[(m, u, c)] for u in units] for m in MODELS]).astype(float)
    qp = np.array([p1.get(("qwenft", u, c), lab[("qwenft", u, c)]) for u in units])
    LAB = np.column_stack([L, qp, L.mean(1)]); FULL = np.column_stack([LAB, TEXT])
    xs = [GOLD.get((u, c)) if u.startswith("G") else None for u in units]
    R = np.array([v is not None for v in xs]).astype(float); xg = np.array([v if v is not None else 0 for v in xs], float); rho = R.mean(); Rb = R == 1
    preds = {"majority vote (no training)": (L.mean(1) > 0.5).astype(float)}
    for name, X in (("labels only", LAB), ("labels + embedding + genre + length", FULL)):
        g = np.zeros(n); lams = []
        for k in range(5):
            tr = Rb & (fold != k); te = fold == k
            g[te], lam = fit_predict(X[tr], xg[tr], X[te]); lams.append(lam)
        preds[f"supervised: {name}"] = g
        PRED.append({"construct": c, "predictor": name, "AUC on human codes (out-of-fold)": roc_auc_score(xg[Rb], g[Rb]),
                     "log loss": log_loss(xg[Rb], np.clip(g[Rb], 1e-4, 1 - 1e-4)), "accuracy": np.mean((g[Rb] >= .5) == xg[Rb]),
                     "majority-vote accuracy": np.mean(preds["majority vote (no training)"][Rb] == xg[Rb]), "penalties chosen": str(lams)})
    gm = xg[Rb].mean(); gse = xg[Rb].std(ddof=1) / np.sqrt(Rb.sum())
    rr = (y_all > 0) & Rb; gr = solve_lin([(np.ones(rr.sum()), xg[rr])], rr)
    RES.append({"construct": c, "estimator": "gold only (100 reviews)", "prevalence": gm, "prevalence SE": gse, "rating coef": gr[0], "rating coef SE": gr[1]})
    for k in ("DMM", "DMM-DSL"):
        d = dmm[(c, k)]; RES.append({"construct": c, "estimator": k, **{x: d[x] for x in ("prevalence", "prevalence SE", "rating coef", "rating coef SE")}})
    for name, g in preds.items():
        e = dsl(g, R, xg, rho)
        RES.append({"construct": c, "estimator": f"DSL, {name}", "prevalence": e[0], "prevalence SE": e[1], "rating coef": e[2], "rating coef SE": e[3]})
    nv = dmm[(c, "naive (majority of groups)")]
    RES.append({"construct": c, "estimator": "naive (majority of groups)", **{x: nv[x] for x in ("prevalence", "prevalence SE", "rating coef", "rating coef SE")}})
RES, PRED = pd.DataFrame(RES), pd.DataFrame(PRED)
base = RES[RES.estimator == "gold only (100 reviews)"].set_index("construct")
RES["SE ratio vs gold only (prevalence)"] = RES.apply(lambda r: r["prevalence SE"] / base.loc[r.construct, "prevalence SE"], axis=1)
RES["SE ratio vs gold only (rating coef)"] = RES.apply(lambda r: r["rating coef SE"] / base.loc[r.construct, "rating coef SE"], axis=1)
RES["effective n of human codes (prevalence)"] = 100 / RES["SE ratio vs gold only (prevalence)"] ** 2
with pd.ExcelWriter(S3 / "Stage3_DSL_results.xlsx") as w:
    RES.to_excel(w, sheet_name="estimates", index=False); PRED.to_excel(w, sheet_name="predictor quality", index=False)
json.dump({"estimates": RES.to_dict("records"), "predictors": PRED.to_dict("records")}, open(O / "dsl_supervised.json", "w"), indent=1, default=float)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(PRED.drop(columns="penalties chosen").round(3).to_string(index=False))
print(RES[["construct", "estimator", "prevalence", "prevalence SE", "SE ratio vs gold only (prevalence)", "rating coef", "rating coef SE", "SE ratio vs gold only (rating coef)"]].round(3).to_string(index=False))
