"""How do estimates and their precision change with the number of human codes (100 / 200 / all 285)?
Human-coded pool: original 100 (blind, current codebook) + Yuhao 100 (AI answers visible while coding) + group 85 (older codebook).
Population sample: 2,900 new reviews + the 285 human-coded reviews = 3,185 units. For each n, a random subset of n human-coded
reviews is treated as labelled (R = 1, rho = n / 3,185); all other units are unlabelled. 200 random subsets for n = 100 and 200;
the full pool for n = 285.
Estimators (as in dmm_dsl.py / dsl_supervised.py): naive majority vote, human codes only, DMM (no human codes), DMM-DSL,
DSL with a cross-fitted supervised predictor (LLM codes + embedding + genre + length; trained only on the labelled subset).
Also: each batch of human codes on its own (source comparison).
Writes Stage3/Stage3_gold_size_results.xlsx, outputs/gold_size.json, figures gold_size_prevalence.png, gold_size_se.png, gold_source.png."""
import json, itertools, time
from pathlib import Path
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
B = Path(r"C:\Users\gujia\Downloads\books"); S3 = B / "Stage3_11.18"; O = S3 / "outputs"; S2 = B / "Stage2_11.16" / "11.17_5modelcomparasion"; FIG = O / "figures"
C6 = ["Absence of Naive Realism", "Theme", "Thought-Provoking", "Ease", "Critic", "Surprise"]; short = lambda c: c.replace("Absence of ", "")
sig = lambda v: 1 / (1 + np.exp(-np.clip(v, -30, 30))); rng = np.random.default_rng(2026)
U = pd.read_csv(S3 / "data" / "stage3_reviews_v2.csv", encoding="utf-8-sig").set_index("unit_id"); units = list(U.index); n = len(units)
SRC = U.source.values; GOLDSRC = ["gold_original", "gold_yuhao", "gold_group"]; isgold = np.isin(SRC, GOLDSRC)
lab, p1 = {}, {}
def add(key, f, idcol, pref=""):
    if not Path(f).exists(): return
    for r in map(json.loads, open(f, encoding="utf-8")):
        if r.get("label") is None: continue
        u = pref + str(r[idcol]); lab[(key, u, r["construct"])] = int(r["label"])
        if "p1" in r: p1[(key, u, r["construct"])] = r["p1"]
for k in ["gemma", "luna", "mini"]:
    add(k, S2 / "outputs" / f"gold_latin_progress_{k}.jsonl", "sample_id", "G"); add(k, O / f"goldfill_{k}.jsonl", "unit_id")
    add(k, O / f"progress_{k}.jsonl", "unit_id"); add(k, O / f"extragold_{k}.jsonl", "unit_id")
add("qwenft", O / "progress_qwenft.jsonl", "unit_id"); add("qwenft", O / "extragold_qwenft.jsonl", "unit_id")
MODELS = ["gemma", "qwenft", "luna", "mini"]; MEMBERS = {"Gemma": ["gemma"], "Qwen-FT": ["qwenft"], "GPT": ["luna", "mini"]}; GR = list(MEMBERS)
miss = [(m, u, c) for m in MODELS for u in units for c in C6 if (m, u, c) not in lab]; assert not miss, f"missing labels: {len(miss)} e.g. {miss[:3]}"
Z = np.load(O / "embeddings_s3_v2.npz"); emb = dict(zip(Z["unit_id"], Z["E"]))
pcs = PCA(5, random_state=0).fit_transform(np.array([emb[u] for u in units]))
gcols = [c for c in U.columns if c.startswith("genre: ") and c != "genre: top"]; G = U.loc[units, gcols].fillna(0).values
logw = np.log(U.loc[units, "n_words"].values.astype(float)); TEXT = np.column_stack([pcs, logw, G])
Dm = (TEXT - TEXT.mean(0)) / np.where(TEXT.std(0) > 0, TEXT.std(0), 1); Xpi = np.column_stack([np.ones(n), Dm])
y_all = U.loc[units, "rating"].values.astype(float); W = np.column_stack([logw, G[:, 1:]]); has_y = np.isfinite(y_all) & (y_all > 0)
prm = {}
for f, idc, pref in [(S2 / "outputs" / "gold_latin_progress_{}.jsonl", "sample_id", "G"), (O / "goldfill_{}.jsonl", "unit_id", ""), (O / "progress_{}.jsonl", "unit_id", ""), (O / "extragold_{}.jsonl", "unit_id", "")]:
    for k in ["gemma", "luna", "mini"]:
        p = Path(str(f).format(k))
        if p.exists():
            for r in map(json.loads, open(p, encoding="utf-8")):
                if r.get("label") is not None: prm[(k, pref + str(r[idc]), r["construct"])] = r["prompt"]

def ridge_logit(X, y, w=None, lam=2.0, beta=None, iters=25):
    m, pp = X.shape; w = np.ones(m) if w is None else w; b = np.zeros(pp) if beta is None else beta.copy(); P = lam * np.eye(pp); P[0, 0] = 0
    for _ in range(iters):
        mu = sig(X @ b); s = w * mu * (1 - mu) + 1e-9
        step = np.linalg.solve(X.T @ (X * s[:, None]) + P, X.T @ (w * (y - mu)) - P @ b); b += step
        if np.abs(step).max() < 1e-6: break
    return b

# ---------- DMM bridge on all 3,185 units (no human codes used) ----------
def dmm_bridge(c, K=5):
    X = {m: np.array([lab[(m, u, c)] for u in units]) for m in MODELS}
    Xm = {}
    for m in MODELS:
        pr = np.array([prm.get((m, u, c), "v1") for u in units]); Xm[m] = np.column_stack([Xpi, pr == "v3", pr == "v4"]).astype(float) if len(set(pr)) > 1 else Xpi
    fold = np.random.default_rng(7).permutation(n) % K; H = np.zeros(n)
    for k in range(K):
        tr, te = fold != k, fold == k; Xt = {m: v[tr] for m, v in X.items()}; Xmt = {m: v[tr] for m, v in Xm.items()}
        des = {m: (np.column_stack([Xmt[m], Xt["luna"]]) if m == "mini" else Xmt[m]) for m in MODELS}
        gm = np.zeros(Xpi.shape[1]); par = {a: {m: np.r_[(1.0 if a else -2.0), np.zeros(des[m].shape[1] - 1)] for m in MODELS} for a in (0, 1)}
        for _ in range(60):
            pi = sig(Xpi[tr] @ gm); l = {}
            for a in (0, 1):
                pr_ = np.ones(tr.sum())
                for m in MODELS: q = sig(des[m] @ par[a][m]); pr_ *= np.where(Xt[m] == 1, q, 1 - q)
                l[a] = pr_ * (pi if a else 1 - pi)
            w = l[1] / (l[1] + l[0] + 1e-300); nn = tr.sum()
            gm = ridge_logit(np.vstack([Xpi[tr], Xpi[tr]]), np.r_[np.ones(nn), np.zeros(nn)], np.r_[w, 1 - w], 2.0, gm, 6)
            for a, ww in ((1, w), (0, 1 - w)):
                for m in MODELS: par[a][m] = ridge_logit(des[m], Xt[m].astype(float), ww, 2.0, par[a][m], 6)
        if np.mean([sig(des[m] @ par[1][m]).mean() - sig(des[m] @ par[0][m]).mean() for m in MODELS]) < 0: par = {0: par[1], 1: par[0]}
        Ms = []
        for g in GR:
            if g == "GPT":
                e = {}
                for a in (0, 1):
                    pl = sig(Xm["luna"][te] @ par[a]["luna"]); pm = [sig(np.column_stack([Xm["mini"][te], np.full(te.sum(), u)]) @ par[a]["mini"]) for u in (0, 1)]
                    e[a] = (pl + (1 - pl) * pm[0] + pl * pm[1]) / 2
                xg = (X["luna"][te] + X["mini"][te]) / 2
            else:
                m = MEMBERS[g][0]; e = {a: sig(Xm[m][te] @ par[a][m]) for a in (0, 1)}; xg = X[m][te]
            d = e[1] - e[0]; Ms.append((xg - e[0]) / np.where(np.abs(d) < 0.05, np.sign(d + 1e-12) * 0.05, d))
        H[te] = 3 * np.mean([Ms[a] * Ms[b] for a, b in itertools.combinations(range(3), 2)], 0) - 2 * Ms[0] * Ms[1] * Ms[2]
    return H

# ---------- DSL helpers ----------
LAMS = [0.3, 1, 3, 10, 30, 100]
def stdz(A, ref):
    m, s = ref.mean(0), ref.std(0); s = np.where(s == 0, 1, s); return (A - m) / s
def fit_predict(Xtr, ytr, Xte):
    inner = np.arange(len(ytr)) % 4; best, bl = 10, np.inf
    for lam in LAMS:
        ll = []
        for f in range(4):
            tr, te = inner != f, inner == f
            if ytr[tr].min() == ytr[tr].max(): continue
            Xs = stdz(Xtr, Xtr[tr]); b = ridge_logit(np.column_stack([np.ones(tr.sum()), Xs[tr]]), ytr[tr], lam=lam, iters=50)
            pr = np.clip(sig(np.column_stack([np.ones(te.sum()), Xs[te]]) @ b), 1e-4, 1 - 1e-4); ll.append(-np.mean(ytr[te] * np.log(pr) + (1 - ytr[te]) * np.log(1 - pr)))
        if ll and np.mean(ll) < bl: bl, best = np.mean(ll), lam
    if ytr.min() == ytr.max(): return np.full(len(Xte), ytr.mean())
    b = ridge_logit(np.column_stack([np.ones(len(ytr)), stdz(Xtr, Xtr)]), ytr, lam=best, iters=50)
    return sig(np.column_stack([np.ones(len(Xte)), stdz(Xte, Xtr)]) @ b)
def solve_lin(terms, idx):
    ni = idx.sum(); Wi = W[idx][:, W[idx].std(0) > 1e-9]   # drop covariates without variation in this sample (e.g. a genre absent from a small subset)
    mk = lambda xv: np.column_stack([np.ones(ni), np.full(ni, xv) if np.isscalar(xv) else xv, Wi]); A = 0; bv = 0
    for wt, xv in terms: Zt = mk(xv); A = A + (Zt * wt[:, None]).T @ Zt / ni; bv = bv + (Zt * wt[:, None]).T @ y_all[idx] / ni
    beta = np.linalg.solve(A, bv); psi = 0
    for wt, xv in terms: Zt = mk(xv); psi = psi + Zt * (wt * (y_all[idx] - Zt @ beta))[:, None]
    Ai = np.linalg.inv(A); return beta[1], np.sqrt(np.diag(Ai @ np.cov(psi.T) @ Ai.T) / ni)[1]
def dsl(g, R, xg, rho):
    ps = g + R / rho * (xg - g); rr = has_y
    reg = solve_lin([(1 - g[rr], 0.0), (g[rr], 1.0), (R[rr] / rho, xg[rr]), (-(R[rr] / rho) * (1 - g[rr]), 0.0), (-(R[rr] / rho) * g[rr], 1.0)], rr)
    return ps.mean(), ps.std(ddof=1) / np.sqrt(n), reg[0], reg[1]

ROWS, SRCROWS = [], []
for c in C6:
    t0 = time.time()
    gx = U.loc[units, f"gold: {c}"].values.astype(float); labelled_pool = np.where(isgold & np.isfinite(gx))[0]
    L = np.column_stack([[lab[(m, u, c)] for u in units] for m in MODELS]).astype(float)
    qp = np.array([p1.get(("qwenft", u, c), lab[("qwenft", u, c)]) for u in units])
    FEAT = np.column_stack([L, qp, L.mean(1), TEXT]); maj = (np.column_stack([L[:, 0], L[:, 1], L[:, 2:4].mean(1) >= 0.5]).mean(1) > 0.5).astype(float)
    H = dmm_bridge(c)
    rows_c = [{"construct": c, "n": 0, "draw": 0, "estimator": "naive (majority vote)", "prevalence": maj.mean(), "prevalence SE": maj.std() / np.sqrt(n), **dict(zip(["rating coef", "rating coef SE"], solve_lin([(np.ones(has_y.sum()), maj[has_y])], has_y)))},
              {"construct": c, "n": 0, "draw": 0, "estimator": "DMM (no human codes)", "prevalence": H.mean(), "prevalence SE": H.std(ddof=1) / np.sqrt(n), **dict(zip(["rating coef", "rating coef SE"], solve_lin([(1 - H[has_y], 0.0), (H[has_y], 1.0)], has_y)))}]
    for nn in (100, 200, len(labelled_pool)):
        draws = 1 if nn == len(labelled_pool) else 200
        for d in range(draws):
            S = labelled_pool if draws == 1 else rng.choice(labelled_pool, nn, replace=False)
            R = np.zeros(n); R[S] = 1; xg = np.where(R == 1, gx, 0.0); xg = np.nan_to_num(xg); rho = R.mean(); Rb = R == 1
            rr = has_y & Rb; go = solve_lin([(np.ones(rr.sum()), xg[rr])], rr) if rr.sum() > 10 else (np.nan, np.nan)
            rows_c.append({"construct": c, "n": nn if draws > 1 else 300, "n_actual": int(Rb.sum()), "draw": d, "estimator": "human codes only", "prevalence": xg[Rb].mean(), "prevalence SE": xg[Rb].std(ddof=1) / np.sqrt(Rb.sum()), "rating coef": go[0], "rating coef SE": go[1]})
            e = dsl(H, R, xg, rho); rows_c.append({"construct": c, "n": nn if draws > 1 else 300, "n_actual": int(Rb.sum()), "draw": d, "estimator": "DMM-DSL", "prevalence": e[0], "prevalence SE": e[1], "rating coef": e[2], "rating coef SE": e[3]})
            fold = np.random.default_rng(100 + d).permutation(n) % 5; g = np.zeros(n)
            for k in range(5):
                tr = Rb & (fold != k); te = fold == k; g[te] = fit_predict(FEAT[tr], xg[tr], FEAT[te])
            e = dsl(g, R, xg, rho); rows_c.append({"construct": c, "n": nn if draws > 1 else 300, "n_actual": int(Rb.sum()), "draw": d, "estimator": "DSL, supervised predictor", "prevalence": e[0], "prevalence SE": e[1], "rating coef": e[2], "rating coef SE": e[3]})
    ROWS += rows_c
    for s in GOLDSRC:   # each batch of human codes on its own
        S = np.where((SRC == s) & np.isfinite(gx))[0]; R = np.zeros(n); R[S] = 1; xg = np.nan_to_num(np.where(R == 1, gx, 0.0)); Rb = R == 1
        fold = np.random.default_rng(5).permutation(n) % 5; g = np.zeros(n)
        for k in range(5):
            tr = Rb & (fold != k); te = fold == k; g[te] = fit_predict(FEAT[tr], xg[tr], FEAT[te])
        e = dsl(g, R, xg, R.mean())
        SRCROWS.append({"construct": c, "source": s, "n": int(Rb.sum()), "human-code prevalence": xg[Rb].mean(), "SE": xg[Rb].std(ddof=1) / np.sqrt(Rb.sum()),
                        "LLM majority on same reviews": maj[Rb].mean(), "agreement with LLM majority": np.mean(maj[Rb] == xg[Rb]), "DSL prevalence": e[0], "DSL SE": e[1]})
    print(c, f"{time.time() - t0:.0f}s", flush=True)
ROWS, SRCROWS = pd.DataFrame(ROWS), pd.DataFrame(SRCROWS)
SUM = ROWS.groupby(["construct", "estimator", "n"]).agg(prevalence=("prevalence", "mean"), mean_SE=("prevalence SE", "mean"), SD_across_draws=("prevalence", "std"),
        rating_coef=("rating coef", "mean"), rating_mean_SE=("rating coef SE", "mean"), rating_SD_across_draws=("rating coef", "std"), draws=("draw", "count"), n_actual=("n_actual", "mean")).reset_index()
with pd.ExcelWriter(S3 / "Stage3_gold_size_results.xlsx") as w:
    SUM.to_excel(w, sheet_name="summary by n", index=False); SRCROWS.to_excel(w, sheet_name="by source of human codes", index=False); ROWS.to_excel(w, sheet_name="all draws", index=False)
json.dump({"summary": SUM.to_dict("records"), "sources": SRCROWS.to_dict("records"), "pool": {s: int((SRC == s).sum()) for s in GOLDSRC}}, open(O / "gold_size.json", "w"), indent=1, default=float)

# ---------- figures ----------
NS = sorted(SUM[SUM.n > 0].n.unique()); NMAX = NS[-1]
EST = [("human codes only", "#1f3864"), ("DSL, supervised predictor", "#c55a11"), ("DMM-DSL", "#7f6000")]
fig, axes = plt.subplots(2, 3, figsize=(10, 6.2), sharex=False)
for ax, c in zip(axes.ravel(), C6):
    s = SUM[SUM.construct == c]; y = 0; ticks, tl = [], []
    for k, col in EST:
        for nn in NS:
            r = s[(s.estimator == k) & (s.n == nn)].iloc[0]; ax.errorbar(r.prevalence, y, xerr=1.96 * r.mean_SE, fmt="o", color=col, ms=3.5, capsize=2, lw=1.1, alpha=0.55 + 0.15 * NS.index(nn))
            ticks.append(y); tl.append(f"{nn}" if nn < 300 else f"all ({int(r.n_actual)})"); y -= 1
        y -= 0.6
    for k, col, ls in (("DMM (no human codes)", "#8faadc", "-"), ("naive (majority vote)", "#7f7f7f", ":")):
        r = s[s.estimator == k].iloc[0]; ax.axvline(r.prevalence, color=col, ls=ls, lw=1.2)
    ax.set_yticks(ticks); ax.set_yticklabels(tl, fontsize=6.5); ax.set_title(short(c), fontsize=9); ax.tick_params(axis="x", labelsize=7); ax.spines[["top", "right"]].set_visible(False)
from matplotlib.lines import Line2D
hd = [Line2D([], [], color=col, marker="o", ls="", label=k) for k, col in EST] + [Line2D([], [], color="#8faadc", label="DMM (no human codes)"), Line2D([], [], color="#7f7f7f", ls=":", label="naive majority vote")]
fig.legend(handles=hd, loc="upper center", ncol=5, fontsize=7.5, frameon=False); fig.text(0.5, 0.01, "estimated share of reviews coded 1 (point and 95% CI; rows = number of human codes)", ha="center", fontsize=8)
plt.tight_layout(rect=[0, 0.03, 1, 0.95]); plt.savefig(FIG / "gold_size_prevalence.png", dpi=200); plt.close()
fig, axes = plt.subplots(1, 2, figsize=(10, 3.4))
for ax, (col_se, ttl) in zip(axes, (("mean_SE", "Share coded 1"), ("rating_mean_SE", "Rating coefficient"))):
    for k, col in EST[:2]:
        v = SUM[(SUM.estimator == k) & (SUM.n > 0)].groupby("n").agg(se=(col_se, "mean"), na=("n_actual", "mean"))
        ax.plot(v.na, v.se, "o-", color=col, label=k)
    v0 = SUM[(SUM.estimator == "human codes only") & (SUM.n == 100)][col_se].mean(); xs = np.array(sorted(SUM[SUM.n > 0].groupby("n").n_actual.mean()))
    ax.plot(xs, v0 * np.sqrt(100 / xs), ls="--", color="grey", lw=1, label="1/√n from 100 human codes")
    ax.set_xticks(xs); ax.set_xticklabels([f"{x:.0f}" for x in xs]); ax.set_xlabel("number of human-coded reviews", fontsize=8); ax.set_ylabel("mean standard error (6 constructs)", fontsize=8); ax.set_title(ttl, fontsize=9)
    ax.legend(fontsize=7, frameon=False); ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.savefig(FIG / "gold_size_se.png", dpi=200); plt.close()
fig, ax = plt.subplots(figsize=(8.5, 3.2)); x = np.arange(len(C6)); cols = {"gold_original": "#1f3864", "gold_yuhao": "#c55a11", "gold_group": "#548235"}
for j, s in enumerate(GOLDSRC):
    d = SRCROWS[SRCROWS.source == s].set_index("construct").loc[C6]
    ax.errorbar(x + (j - 1) * 0.22, d["human-code prevalence"], yerr=1.96 * d["SE"], fmt="o", color=cols[s], capsize=2, label={"gold_original": "original 100 (blind)", "gold_yuhao": "Yuhao 100 (AI visible)", "gold_group": "group 85 (older codebook)"}[s])
    ax.plot(x + (j - 1) * 0.22, d["LLM majority on same reviews"], "x", color=cols[s], ms=6)
ax.set_xticks(x); ax.set_xticklabels([short(c) for c in C6], fontsize=8); ax.set_ylabel("share coded 1 (95% CI)\n× = LLM majority, same reviews", fontsize=8)
ax.legend(fontsize=7, frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.15)); ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.savefig(FIG / "gold_source.png", dpi=200); plt.close()
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 20)
print(SUM[SUM.estimator.isin(["human codes only", "DSL, supervised predictor", "DMM-DSL"])].round(3).to_string(index=False)); print(SRCROWS.round(3).to_string(index=False))
