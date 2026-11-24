"""Stage 3: DMM and DMM-assisted DSL (Egami & Shin 2026, arXiv 2608.18294v2) on 3,000 Goodreads reviews.
Usage: python dmm_dsl.py [groups]   groups = comma list from Sonnet,Gemma,Qwen-FT,GPT (default: all available)
Proxies are GROUPS (Sec. 5.1): Sonnet | Gemma | Qwen-FT | GPT (= mean of GPT-6 Luna and GPT-5.4 mini; within-group dependence allowed).
D (conditioning covariates) = 5 embedding PCs + log review length + genre vote shares (+ each group's own prompt in its error model).
Nuisance: latent class model with covariates, P(X*=1|D) and group error rates eta_{g,a}(D) by ridge-penalised EM, 5-fold cross-fitting.
  GPT group: P(Luna|a,D) * P(mini|a,D,Luna);  eta_{GPT,a} = E[(Luna + mini)/2 | a, D].
Bridge: M_g = (X_g - eta_{g,0}) / (eta_{g,1} - eta_{g,0});  robust bridge H^R = 3*mean pair products - 2*mean triple products (eq. 3.7).
Estimators for each construct (Change excluded: 3% prevalence):
  naive (majority of groups), gold-only (100 human-coded reviews), DMM (eq. 3.10, no gold labels), DMM-DSL (eq. 5.1, rho = n_gold / n).
Targets: (1) prevalence E[X*]; (2) linear regression of star rating on X* + log length + genre shares (rating > 0).
Diagnostics with the same D: (a) gold residual moments (Sec. 5.3); (b) between-group overidentification test, parametric bootstrap (Sec. 5.2);
(c) prevalence from each 3-group subset.
Writes Stage3/Stage3_DMM_DSL_results[_tag].xlsx and outputs/dmm_dsl[_tag].json."""
import sys, os, json, csv, itertools, time
from math import erf, sqrt
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.decomposition import PCA
B = Path(r"C:\Users\gujia\Downloads\books"); S3 = B / "Stage3_11.18"; O = S3 / "outputs"; S2 = B / "Stage2_11.16" / "11.17_5modelcomparasion"
F = B / "Stage2_11.16" / "11.16_humanAIcomparasion_finetune"
C6 = ["Absence of Naive Realism", "Theme", "Thought-Provoking", "Ease", "Critic", "Surprise"]
import os as _os
QUICK = _os.environ.get("QUICK") == "1"
if QUICK: C6 = C6[:2]
rng = np.random.default_rng(2026); sig = lambda v: 1 / (1 + np.exp(-np.clip(v, -30, 30)))
pval = lambda z: 2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2))))
MEMBERS = {"Sonnet": ["sonnet"], "Gemma": ["gemma"], "Qwen-FT": ["qwenft"], "GPT": ["luna", "mini"]}
SINGLE = {"Luna": ["luna"], "Mini": ["mini"]}  # used only in the subset diagnostic

# ---------------- data ----------------
U = pd.read_csv(S3 / "data" / "stage3_reviews.csv", encoding="utf-8-sig"); U = U.set_index("unit_id")
gold_items = {it["review_id"]: it["labels"] for it in json.load(open(F / "data" / "dataset.json", encoding="utf-8"))["items"]}
GOLD = {(f"G{r}", c): v for r, l in gold_items.items() for c, v in l.items()}
lab, prm = {}, {}
def add(key, f, idcol, pref=""):
    if not Path(f).exists(): return
    for r in map(json.loads, open(f, encoding="utf-8")):
        if r.get("label") is None: continue
        u = pref + str(r[idcol]); lab[(key, u, r["construct"])] = int(r["label"]); prm[(key, u, r["construct"])] = r.get("prompt", "v1")
for k in ["sonnet", "gemma", "luna", "mini"]:
    add(k, S2 / "outputs" / f"gold_latin_progress_{k}.jsonl", "sample_id", "G")
    add(k, O / f"goldfill_{k}.jsonl", "unit_id"); add(k, O / f"progress_{k}.jsonl", "unit_id")
add("qwenft", O / "progress_qwenft.jsonl", "unit_id")
avail = [g for g, ms in MEMBERS.items() if all(sum(1 for x in lab if x[0] == m) > 19000 for m in ms)]
GR = sys.argv[1].split(",") if len(sys.argv) > 1 else avail
DSPEC = os.environ.get("DSPEC", "full")  # "full" = embedding + length + genre; "nogenre" = embedding + length (genre removed)
MEMBERS.update(SINGLE)
TAG = ("" if set(GR) == set(MEMBERS) - set(SINGLE) else "_" + "-".join(GR)) + ("" if DSPEC == "full" else "_" + DSPEC)
print("groups:", GR, "| D:", os.environ.get("DSPEC", "full"), flush=True)
Z = np.load(O / "embeddings_s3.npz"); emb = dict(zip(Z["unit_id"], Z["E"]))
units = [u for u in U.index if all((m, u, c) in lab for g in GR for m in MEMBERS[g] for c in C6)]
print("units with complete labels:", len(units), "of", len(U), flush=True)
pcs = PCA(5, random_state=0).fit_transform(np.array([emb[u] for u in units]))
gcols = [c for c in U.columns if c.startswith("genre: ") and c != "genre: top"]
Dmat = np.column_stack([pcs, np.log(U.loc[units, "n_words"].values)] + ([U.loc[units, gcols].values] if DSPEC == "full" else []))
Dmat = (Dmat - Dmat.mean(0)) / np.where(Dmat.std(0) > 0, Dmat.std(0), 1)
Xpi = np.column_stack([np.ones(len(units)), Dmat]); n = len(units)
isgold = np.array([u.startswith("G") for u in units])

def ridge_logit(X, y, w=None, lam=2.0, beta=None, iters=25):
    m, p = X.shape; w = np.ones(m) if w is None else w; b = np.zeros(p) if beta is None else beta.copy()
    P = lam * np.eye(p); P[0, 0] = 0
    for _ in range(iters):
        mu = sig(X @ b); s = w * mu * (1 - mu) + 1e-9
        step = np.linalg.solve(X.T @ (X * s[:, None]) + P, X.T @ (w * (y - mu)) - P @ b); b += step
        if np.abs(step).max() < 1e-6: break
    return b

def design(c, idx=None):
    """X: per-model labels; Xm: per-model error-model design (D + own prompt dummies)."""
    idx = np.arange(n) if idx is None else idx; X, Xm = {}, {}
    for g in GR:
        for m in MEMBERS[g]:
            X[m] = np.array([lab[(m, units[i], c)] for i in idx]); pr = np.array([prm[(m, units[i], c)] for i in idx])
            Xm[m] = np.column_stack([Xpi[idx], pr == "v3", pr == "v4"]).astype(float) if len(set(pr)) > 1 else Xpi[idx]
    return X, Xm

def member_p(par, Xm, X, a, m):
    if m == "mini" and "luna" in par[a]: return sig(np.column_stack([Xm[m], X["luna"]]) @ par[a][m])
    return sig(Xm[m] @ par[a][m])

def fit(X, Xm, Xp, groups, iters=60, lam=2.0):
    mods = [m for g in groups for m in MEMBERS[g]]; nn = len(Xp)
    des = {m: (np.column_stack([Xm[m], X["luna"]]) if m == "mini" and "luna" in mods else Xm[m]) for m in mods}
    gm = np.zeros(Xp.shape[1]); par = {a: {m: np.r_[(1.0 if a else -2.0), np.zeros(des[m].shape[1] - 1)] for m in mods} for a in (0, 1)}
    for _ in range(iters):
        pi = sig(Xp @ gm); l = {}
        for a in (0, 1):
            pr = np.ones(nn)
            for m in mods: p = sig(des[m] @ par[a][m]); pr *= np.where(X[m] == 1, p, 1 - p)
            l[a] = pr * (pi if a else 1 - pi)
        w = l[1] / (l[1] + l[0] + 1e-300)
        gm = ridge_logit(np.vstack([Xp, Xp]), np.r_[np.ones(nn), np.zeros(nn)], np.r_[w, 1 - w], lam, gm, 6)
        for a, ww in ((1, w), (0, 1 - w)):
            for m in mods: par[a][m] = ridge_logit(des[m], X[m].astype(float), ww, lam, par[a][m], 6)
    if np.mean([sig(des[m] @ par[1][m]).mean() - sig(des[m] @ par[0][m]).mean() for m in mods]) < 0:   # anchoring rule
        gm = -gm; par = {0: par[1], 1: par[0]}
    return gm, par

def eta_group(par, Xm, g, a):
    if g == "GPT":
        pl = sig(Xm["luna"] @ par[a]["luna"]); pm = [sig(np.column_stack([Xm["mini"], np.full(len(pl), u)]) @ par[a]["mini"]) for u in (0, 1)]
        return (pl + (1 - pl) * pm[0] + pl * pm[1]) / 2
    m = MEMBERS[g][0]; return sig(Xm[m] @ par[a][m])

def robust_bridge(Ms):
    J = len(Ms); pairs = list(itertools.combinations(range(J), 2)); trip = list(itertools.combinations(range(J), 3))
    H2 = np.mean([Ms[a] * Ms[b] for a, b in pairs], 0); H3 = np.mean([Ms[a] * Ms[b] * Ms[d] for a, b, d in trip], 0)
    return 3 * H2 - 2 * H3

def cross_fit_bridge(c, groups, K=5):
    X, Xm = design(c); H = np.zeros(n); fold = np.random.default_rng(7).permutation(n) % K; post = np.zeros(n)
    for k in range(K):
        tr, te = fold != k, fold == k
        gm, par = fit({m: v[tr] for m, v in X.items()}, {m: v[tr] for m, v in Xm.items()}, Xpi[tr], groups)
        Xt, Xmt = {m: v[te] for m, v in X.items()}, {m: v[te] for m, v in Xm.items()}
        Ms = []
        for g in groups:
            e1, e0 = eta_group(par, Xmt, g, 1), eta_group(par, Xmt, g, 0)
            xg = np.mean([Xt[m] for m in MEMBERS[g]], 0); Ms.append((xg - e0) / np.where(np.abs(e1 - e0) < 0.05, np.sign(e1 - e0 + 1e-12) * 0.05, e1 - e0))
        H[te] = robust_bridge(Ms) if len(groups) >= 3 else np.mean(Ms, 0)
    return H, X

# ---------------- downstream estimators ----------------
y_all = U.loc[units, "rating"].values.astype(float)
W = np.column_stack([np.log(U.loc[units, "n_words"].values), U.loc[units, gcols].values[:, 1:]])  # drop first genre (shares sum to 1)
def solve_lin(wts_terms, idx):
    """wts_terms: list of (weight_vector, x_value) ; moment sum_t w_t Z_t (y - Z_t b). Returns beta, psi_i matrix."""
    A = 0; bvec = 0
    for wt, xv in wts_terms:
        Zt = np.column_stack([np.ones(idx.sum()), np.full(idx.sum(), xv) if np.isscalar(xv) else xv, W[idx]])
        A = A + (Zt * wt[:, None]).T @ Zt / idx.sum(); bvec = bvec + (Zt * wt[:, None]).T @ y_all[idx] / idx.sum()
    beta = np.linalg.solve(A, bvec); psi = 0
    for wt, xv in wts_terms:
        Zt = np.column_stack([np.ones(idx.sum()), np.full(idx.sum(), xv) if np.isscalar(xv) else xv, W[idx]])
        psi = psi + Zt * (wt * (y_all[idx] - Zt @ beta))[:, None]
    Ainv = np.linalg.inv(A); V = np.cov(psi.T); se = np.sqrt(np.diag(Ainv @ V @ Ainv.T) / idx.sum())
    return beta[1], se[1]

RES, DIAG = [], []
for c in C6:
    t0 = time.time()
    H, X = cross_fit_bridge(c, GR)
    xs = np.array([GOLD.get((u, c)) for u in units], dtype=object); R = np.array([v is not None for v in xs]) & isgold
    xg = np.array([v if v is not None else 0 for v in xs], float); rho = R.mean()
    groups_lab = np.column_stack([np.mean([X[m] for m in MEMBERS[g]], 0) >= 0.5 for g in GR]).astype(float)
    maj = (groups_lab.mean(1) > 0.5).astype(float)
    est = {}
    est["naive (majority of groups)"] = (maj.mean(), maj.std() / np.sqrt(n))
    est["gold only (100 reviews)"] = (xg[R].mean(), xg[R].std(ddof=1) / np.sqrt(R.sum()))
    est["DMM"] = (H.mean(), H.std(ddof=1) / np.sqrt(n))
    ps = H + R / rho * (xg - H); est["DMM-DSL"] = (ps.mean(), ps.std(ddof=1) / np.sqrt(n))
    rr = y_all > 0; Rr = R & rr
    reg = {"naive (majority of groups)": solve_lin([(np.ones(rr.sum()), maj[rr])], rr),
           "gold only (100 reviews)": solve_lin([(np.ones(Rr.sum()), xg[Rr])], Rr),
           "DMM": solve_lin([(1 - H[rr], 0.0), (H[rr], 1.0)], rr),
           "DMM-DSL": solve_lin([(1 - H[rr], 0.0), (H[rr], 1.0), (R[rr] / rho, xg[rr]), (-(R[rr] / rho) * (1 - H[rr]), 0.0), (-(R[rr] / rho) * H[rr], 1.0)], rr)}
    for k in est:
        RES.append({"construct": c, "estimator": k, "prevalence": est[k][0], "prevalence SE": est[k][1],
                    "rating coef": reg[k][0], "rating coef SE": reg[k][1]})
    # DMM bridge check on gold: E[H | X*] should equal X*
    DIAG.append({"construct": c, "mean H | gold X*=1": H[R & (xg == 1)].mean(), "mean H | gold X*=0": H[R & (xg == 0)].mean(),
                 "n gold": int(R.sum()), "H min": H.min(), "H max": H.max()})
    print(c, f"{time.time() - t0:.0f}s", {k: round(v[0], 3) for k, v in est.items()}, flush=True)
RES, DIAG = pd.DataFrame(RES), pd.DataFrame(DIAG)

# ---------------- CI diagnostics with D = embedding + length + genre + prompt ----------------
def bvr(X, Xm, gm, par, groups, Xp):
    pi = sig(Xp @ gm); cat = {}
    for g in groups:
        for a in (0, 1):
            if g == "GPT":
                pl = sig(Xm["luna"] @ par[a]["luna"]); pm = [sig(np.column_stack([Xm["mini"], np.full(len(pl), u)]) @ par[a]["mini"]) for u in (0, 1)]
                cat[(g, a)] = np.column_stack([(1 - pl) * (1 - pm[0]), (1 - pl) * pm[0], pl * (1 - pm[1]), pl * pm[1]])
            else:
                p = sig(Xm[MEMBERS[g][0]] @ par[a][MEMBERS[g][0]]); cat[(g, a)] = np.column_stack([1 - p, p])
    obs = {g: (2 * X["luna"] + X["mini"] if g == "GPT" else X[MEMBERS[g][0]]) for g in groups}; tot, per = 0.0, {}
    for g1, g2 in itertools.combinations(groups, 2):
        st = 0.0
        for u in range(cat[(g1, 0)].shape[1]):
            for v in range(cat[(g2, 0)].shape[1]):
                E = (pi * cat[(g1, 1)][:, u] * cat[(g2, 1)][:, v] + (1 - pi) * cat[(g1, 0)][:, u] * cat[(g2, 0)][:, v]).sum()
                st += (((obs[g1] == u) & (obs[g2] == v)).sum() - E) ** 2 / max(E, 1e-6)
        per[f"{g1} – {g2}"] = st; tot += st
    return tot, per

def simulate(gm, par, Xm, Xp, groups):
    z = rng.random(len(Xp)) < sig(Xp @ gm); X = {}
    for g in groups:
        for m in MEMBERS[g]:
            if m == "mini": continue
            p = np.where(z, sig(Xm[m] @ par[1][m]), sig(Xm[m] @ par[0][m])); X[m] = (rng.random(len(z)) < p).astype(int)
    if "GPT" in groups:
        pm = np.where(z, sig(np.column_stack([Xm["mini"], X["luna"]]) @ par[1]["mini"]), sig(np.column_stack([Xm["mini"], X["luna"]]) @ par[0]["mini"]))
        X["mini"] = (rng.random(len(z)) < pm).astype(int)
    return X

CI = []
for c in C6:
    X, Xm = design(c); gm, par = fit(X, Xm, Xpi, GR); NPROX = sum(len(MEMBERS[g]) for g in GR)
    T, per = bvr(X, Xm, gm, par, GR, Xpi) if NPROX >= 4 else (np.nan, {})
    pv_ = np.nan
    if NPROX >= 4:
        Tb = [bvr(Xb, Xm, *fit(Xb, Xm, Xpi, GR, iters=30), GR, Xpi)[0] for Xb in (simulate(gm, par, Xm, Xpi, GR) for _ in range(2 if QUICK else 60))]
        pv_ = (np.sum(np.array(Tb) >= T) + 1) / (len(Tb) + 1)
    subs = list(itertools.combinations(GR, 3)) if len(GR) >= 4 else [tuple([g for g in GR if g != "GPT"] + [x]) for x in ("GPT", "Luna", "Mini")]; sub = {" + ".join(s): sig(Xpi @ fit(X, Xm, Xpi, list(s))[0]).mean() for s in subs}
    # gold residual moments between groups (cross-fitted eta given X*, D)
    gi = np.where(isgold)[0]; gi = gi[[GOLD.get((units[i], c)) is not None for i in gi]]; cls = np.array([GOLD[(units[i], c)] for i in gi])
    res = {}
    for g in GR:
        xg_ = np.mean([X[m][gi] for m in MEMBERS[g]], 0); eta = np.zeros(len(gi)); fold = np.random.default_rng(1).permutation(len(gi)) % 5
        Xd = Xm[MEMBERS[g][0]][gi]
        for f in range(5):
            for a in (0, 1):
                tr = (fold != f) & (cls == a); te = (fold == f) & (cls == a)
                if te.sum() == 0: continue
                yy = (xg_[tr] >= 0.5).astype(float)
                eta[te] = yy.mean() if (tr.sum() < 3 or yy.min() == yy.max()) else sig(Xd[te] @ ridge_logit(Xd[tr], yy, lam=4.0))
        res[g] = (xg_ >= 0.5) - eta
    gp = []
    for g1, g2 in itertools.combinations(GR, 2):
        mi = res[g1] * res[g2]; gp.append((mi.mean() / np.sqrt((res[g1] ** 2).mean() * (res[g2] ** 2).mean()), pval(mi.mean() / (mi.std(ddof=1) / np.sqrt(len(mi))))))
    CI.append({"construct": c, "overidentification BVR": T, "bootstrap p": pv_, "worst pair": max(per, key=per.get) if per else "",
               "subset prevalence min": min(sub.values()), "subset prevalence max": max(sub.values()),
               "gold residual corr median": np.median([x[0] for x in gp]), "gold pairs p<.05": sum(x[1] < .05 for x in gp), "gold pairs": len(gp), **sub})
    print("diag", c, flush=True)
CI = pd.DataFrame(CI)
with pd.ExcelWriter(S3 / f"Stage3_DMM_DSL_results{TAG}.xlsx") as w:
    RES.to_excel(w, sheet_name="estimates", index=False); DIAG.to_excel(w, sheet_name="bridge check (gold)", index=False)
    CI.to_excel(w, sheet_name="CI diagnostics", index=False)
json.dump({"groups": GR, "n": n, "estimates": RES.to_dict("records"), "bridge": DIAG.to_dict("records"), "ci": CI.to_dict("records")},
          open(O / f"dmm_dsl{TAG}.json", "w"), indent=1, default=float)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(RES.round(3).to_string(index=False)); print(DIAG.round(3).to_string(index=False))
print(CI[["construct", "bootstrap p", "worst pair", "subset prevalence min", "subset prevalence max", "gold residual corr median", "gold pairs p<.05", "gold pairs"]].round(3).to_string(index=False))
