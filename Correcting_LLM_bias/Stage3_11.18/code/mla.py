"""Maximum Likelihood Adjustment (MLA; TeBlunthuis, Hase & Chan 2024, Appendix E; Carroll et al. 2006) for misclassified LLM codes.
W = the automated classification = majority vote of the three LLM coder groups (Gemma | Qwen-FT | GPT); X = true (human) code;
Z = covariates (log review length + genre shares, first genre dropped); Y = star rating.
(1) Share coded 1: L = prod_i  p(w_i | x, z_i) p(x | z_i)  [x observed for human-coded reviews, summed over x = 0, 1 otherwise];
    error model logit p(W=1 | x, z) = a0 + a1 x + a'z; exposure model logit p(X=1 | z) = g0 + g'z; estimate = mean_i p(X=1 | z_i).
(2) Rating effect: L = prod_i f(y_i | x, z_i) p(w_i | x, y_i, z_i) p(x | z_i); f = multinomial logit of the 1-5 star rating (a Gaussian f lets the
    x-mixture fit the skewed discrete rating distribution and gives spurious effects); reported as the average marginal effect of x on the
    expected rating (stars), comparable to the linear-regression coefficient of the other estimators. Error model includes y. Ratings > 0 only.
Standard errors from the observed Fisher information (numerical Hessian of the log-likelihood; delta method for the share).
Part A: 3,000 reviews with the original 100 human codes (comparable to dsl_supervised.py).
Part B: 3,185 reviews, 100 / 200 / all human codes from the pooled 274 (50 random subsets for 100 and 200), comparable to gold_size.py.
Writes Stage3/Stage3_MLA_results.xlsx and outputs/mla.json."""
import json, sys, time
from pathlib import Path
import numpy as np, pandas as pd
from scipy.optimize import minimize
B = Path(r"C:\Users\gujia\Downloads\books"); S3 = B / "Stage3_11.18"; O = S3 / "outputs"; S2 = B / "Stage2_11.16" / "11.17_5modelcomparasion"
C6 = ["Absence of Naive Realism", "Theme", "Thought-Provoking", "Ease", "Critic", "Surprise"]
rng = np.random.default_rng(2026); NDRAW = 20
U = pd.read_csv(S3 / "data" / "stage3_reviews_v2.csv", encoding="utf-8-sig").set_index("unit_id")
lab = {}
def add(key, f, idcol, pref=""):
    if not Path(f).exists(): return
    for r in map(json.loads, open(f, encoding="utf-8")):
        if r.get("label") is not None: lab[(key, pref + str(r[idcol]), r["construct"])] = int(r["label"])
for k in ["gemma", "luna", "mini"]:
    add(k, S2 / "outputs" / f"gold_latin_progress_{k}.jsonl", "sample_id", "G"); add(k, O / f"goldfill_{k}.jsonl", "unit_id")
    add(k, O / f"progress_{k}.jsonl", "unit_id"); add(k, O / f"extragold_{k}.jsonl", "unit_id")
add("qwenft", O / "progress_qwenft.jsonl", "unit_id"); add("qwenft", O / "extragold_qwenft.jsonl", "unit_id")
gcols = [c for c in U.columns if c.startswith("genre: ") and c != "genre: top"]
def setup(units):
    Zr = np.column_stack([np.log(U.loc[units, "n_words"].values.astype(float)), U.loc[units, gcols].fillna(0).values[:, 1:]])
    keep = Zr.std(0) > 1e-9; Zr = Zr[:, keep]; Z = (Zr - Zr.mean(0)) / Zr.std(0)
    y = U.loc[units, "rating"].values.astype(float); hy = np.isfinite(y) & (y > 0)
    return Z, y, hy
def wvote(units, c):
    g = np.column_stack([[lab[("gemma", u, c)] for u in units], [lab[("qwenft", u, c)] for u in units],
                         (np.array([lab[("luna", u, c)] for u in units]) + np.array([lab[("mini", u, c)] for u in units])) / 2 >= 0.5])
    return (g.mean(1) > 0.5).astype(float)

def lse(a, b): m = np.maximum(a, b); return m + np.log(np.exp(a - m) + np.exp(b - m))
def logsig(v): return -np.logaddexp(0, -v)
def loglik_prev(th, Z, w, R, x, per=False):
    k = Z.shape[1]; a0, a1, a = th[0], th[1], th[2:2 + k]; g0, g = th[2 + k], th[3 + k:3 + 2 * k]
    ex = g0 + Z @ g; ew = a0 + Z @ a
    def lw(xv): e = ew + a1 * xv; return np.where(w == 1, logsig(e), logsig(-e))
    lx1, lx0 = logsig(ex), logsig(-ex)
    obs = np.where(x == 1, lw(1) + lx1, lw(0) + lx0); mis = lse(lw(1) + lx1, lw(0) + lx0)
    v = np.where(R == 1, obs, mis); return v if per else np.sum(v)
def loglik_reg(th, Z, w, R, x, y, per=False):
    """Main model: categorical (multinomial logit) rating 1..5 given x and z -- avoids the Gaussian-mixture artefact on discrete ratings."""
    k = Z.shape[1]; K = 5; nb = 2 + k; Bm = th[:4 * nb].reshape(4, nb); o = 4 * nb
    a0, a1, ay, a = th[o], th[o + 1], th[o + 2], th[o + 3:o + 3 + k]; o2 = o + 3 + k; g0, g = th[o2], th[o2 + 1:o2 + 1 + k]
    yi = y.astype(int) - 1; ys = (y - 3.0) / 1.0
    def lf(xv):
        eta = np.column_stack([np.zeros(len(Z))] + [Bm[j, 0] + Bm[j, 1] * xv + Z @ Bm[j, 2:] for j in range(4)])
        eta = eta - eta.max(1, keepdims=True); lp = eta - np.log(np.exp(eta).sum(1, keepdims=True)); return lp[np.arange(len(Z)), yi]
    def lw(xv): e = a0 + a1 * xv + ay * ys + Z @ a; return np.where(w == 1, logsig(e), logsig(-e))
    ex = g0 + Z @ g; lx1, lx0 = logsig(ex), logsig(-ex)
    obs = np.where(x == 1, lf(1) + lw(1) + lx1, lf(0) + lw(0) + lx0); mis = lse(lf(1) + lw(1) + lx1, lf(0) + lw(0) + lx0)
    v = np.where(R == 1, obs, mis); return v if per else np.sum(v)
def mean_rating_effect(th, Z):
    """Average marginal effect of x on the expected rating: mean_i (E[Y|x=1,z_i] - E[Y|x=0,z_i])."""
    k = Z.shape[1]; nb = 2 + k; Bm = th[:4 * nb].reshape(4, nb); vals = np.arange(1, 6)
    def ey(xv):
        eta = np.column_stack([np.zeros(len(Z))] + [Bm[j, 0] + Bm[j, 1] * xv + Z @ Bm[j, 2:] for j in range(4)])
        eta = eta - eta.max(1, keepdims=True); pr = np.exp(eta); pr /= pr.sum(1, keepdims=True); return pr @ vals
    return float(np.mean(ey(1) - ey(0)))
def hessian(f, th, h=1e-4):
    p = len(th); H = np.zeros((p, p)); f0 = f(th)
    for i in range(p):
        for j in range(i, p):
            e_i = np.zeros(p); e_i[i] = h; e_j = np.zeros(p); e_j[j] = h
            H[i, j] = H[j, i] = (f(th + e_i + e_j) - f(th + e_i - e_j) - f(th - e_i + e_j) + f(th - e_i - e_j)) / (4 * h * h)
    return H
OPG = False   # Part B: outer product of per-review scores instead of the full numerical Hessian (much faster, same large-sample information)
def fit(ll, p0, llv=None):
    r = minimize(lambda t: -ll(t), p0, method="L-BFGS-B")
    if OPG and llv is not None:
        h = 1e-5; Sc = np.column_stack([(llv(r.x + e) - llv(r.x - e)) / (2 * h) for e in np.eye(len(r.x)) * h]); cov = np.linalg.pinv(Sc.T @ Sc)
    else:
        H = hessian(ll, r.x); cov = np.linalg.pinv(-H)
    return r.x, cov
def mla_prev(Z, w, R, x, p0=None):
    k = Z.shape[1]; p00 = np.r_[-1.5, 3.0, np.zeros(k), np.log(np.mean(x[R == 1]) / (1 - np.mean(x[R == 1])) + 1e-9), np.zeros(k)]
    p0 = p0 if p0 is not None else p00; ll = lambda t: loglik_prev(t, Z, w, R, x); th, cov = fit(ll, p0, lambda t: loglik_prev(t, Z, w, R, x, True)); global LAST_PREV; LAST_PREV = th
    gi = slice(2 + k, 3 + 2 * k); ex = 1 / (1 + np.exp(-(th[2 + k] + Z @ th[3 + k:3 + 2 * k]))); est = ex.mean()
    grad = np.zeros(len(th)); D = np.column_stack([np.ones(len(Z)), Z]) * (ex * (1 - ex))[:, None]; grad[gi] = D.mean(0)
    return est, float(np.sqrt(max(grad @ cov @ grad, 0)))
def mla_reg(Z, w, R, x, y, p0=None):
    k = Z.shape[1]; nb = 2 + k
    freq = np.bincount(y.astype(int) - 1, minlength=5) + 1; base = np.log(freq[1:] / freq[0])
    p0 = p0 if p0 is not None else np.r_[np.concatenate([np.r_[base[j], 0, np.zeros(k)] for j in range(4)]), -1.5, 3.0, 0, np.zeros(k), 0, np.zeros(k)]
    ll = lambda t: loglik_reg(t, Z, w, R, x, y); th, cov = fit(ll, p0, lambda t: loglik_reg(t, Z, w, R, x, y, True)); global LAST_REG; LAST_REG = th
    eff = mean_rating_effect(th, Z); h = 1e-4; grad = np.zeros(len(th))
    for j in range(4 * nb):   # delta method: only the main-model parameters enter the effect
        e = np.zeros(len(th)); e[j] = h; grad[j] = (mean_rating_effect(th + e, Z) - mean_rating_effect(th - e, Z)) / (2 * h)
    return eff, float(np.sqrt(max(grad @ cov @ grad, 0)))

OUT = []
# ---------- Part A: 3,000 reviews, original 100 human codes ----------
unitsA = [u for u in U.index if U.loc[u, "source"] in ("new", "gold_original")]; ZA, yA, hyA = setup(unitsA)
for c in C6:
    t0 = time.time(); w = wvote(unitsA, c); gx = U.loc[unitsA, f"gold: {c}"].values.astype(float)
    R = (np.isfinite(gx)).astype(float); x = np.nan_to_num(gx)
    pe, pse = mla_prev(ZA, w, R, x); re_, rse = mla_reg(ZA[hyA], w[hyA], R[hyA], x[hyA], yA[hyA])
    OUT.append({"part": "A (original 100)", "construct": c, "n": int(R.sum()), "draw": 0, "prevalence": pe, "prevalence SE": pse, "rating coef": re_, "rating coef SE": rse})
    print("A", c, round(pe, 3), round(pse, 3), round(re_, 3), round(rse, 3), f"{time.time() - t0:.0f}s", flush=True)
# ---------- Part B: 3,185 reviews, 100 / 200 / all pooled human codes ----------
OPG = True
unitsB = list(U.index); ZB, yB, hyB = setup(unitsB); isg = U.source.isin(["gold_original", "gold_yuhao", "gold_group"]).values
for c in C6:
    t0 = time.time(); w = wvote(unitsB, c); gx = U.loc[unitsB, f"gold: {c}"].values.astype(float); pool = np.where(isg & np.isfinite(gx))[0]
    for nn in (len(pool), 100, 200):   # full pool first: its estimates are the warm start for the random subsets
        for d in range(1 if nn == len(pool) else NDRAW):
            S = pool if nn == len(pool) else rng.choice(pool, nn, replace=False); R = np.zeros(len(unitsB)); R[S] = 1; x = np.nan_to_num(np.where(R == 1, gx, 0))
            try:
                ws = nn != len(pool); pe, pse = mla_prev(ZB, w, R, x, P0P if ws else None); re_, rse = mla_reg(ZB[hyB], w[hyB], R[hyB], x[hyB], yB[hyB], P0R if ws else None)
                if not ws: P0P, P0R = LAST_PREV.copy(), LAST_REG.copy()
            except Exception as e:
                pe = pse = re_ = rse = np.nan
            OUT.append({"part": "B (pooled)", "construct": c, "n": nn if nn != len(pool) else 300, "n_actual": int(R.sum()), "draw": d,
                        "prevalence": pe, "prevalence SE": pse, "rating coef": re_, "rating coef SE": rse})
    print("B", c, f"{time.time() - t0:.0f}s", flush=True)
OUT = pd.DataFrame(OUT)
SUM = OUT[OUT.part == "B (pooled)"].groupby(["construct", "n"]).agg(prevalence=("prevalence", "mean"), mean_SE=("prevalence SE", "mean"), SD_across_draws=("prevalence", "std"),
        rating_coef=("rating coef", "mean"), rating_mean_SE=("rating coef SE", "mean"), rating_SD_across_draws=("rating coef", "std"), draws=("draw", "count"), n_actual=("n_actual", "mean")).reset_index()
with pd.ExcelWriter(S3 / "Stage3_MLA_results.xlsx") as w_:
    OUT[OUT.part.str.startswith("A")].to_excel(w_, sheet_name="A original 100", index=False); SUM.to_excel(w_, sheet_name="B summary by n", index=False)
    OUT[OUT.part.str.startswith("B")].to_excel(w_, sheet_name="B all draws", index=False)
json.dump({"A": OUT[OUT.part.str.startswith("A")].to_dict("records"), "B": SUM.to_dict("records")}, open(O / "mla.json", "w"), indent=1, default=float)
pd.set_option("display.width", 250); print(OUT[OUT.part.str.startswith("A")].round(3).to_string(index=False)); print(SUM.round(3).to_string(index=False))
