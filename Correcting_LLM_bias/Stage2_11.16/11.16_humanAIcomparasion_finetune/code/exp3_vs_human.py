"""Experiment 3 models (prompt v2, zero-shot) vs human codes on the 100 human-coded reviews; 500 bootstrap CIs."""
import json, random
from pathlib import Path
import numpy as np
from sklearn.metrics import cohen_kappa_score, precision_score, recall_score, f1_score
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "exp3_vs_human"; OUT.mkdir(parents=True, exist_ok=True)
B, SEED = 500, 2026
data = json.load(open(ROOT / "data" / "dataset.json", encoding="utf-8"))
C, ITEMS = data["constructs"], data["items"]
RIDS = [it["review_id"] for it in ITEMS]
gold = {(it["review_id"], c): it["labels"][c] for it in ITEMS for c in C}
MODELS = {"GPT-4o": "gpt4o", "Sonnet 5.5": "sonnet", "Qwen3-14B": "qwen", "Gemma 3 12B": "gemma"}
pred = {}
for name, key in MODELS.items():
    d = {}
    for r in map(json.loads, open(ROOT / "data" / f"exp3_labels_{key}.jsonl", encoding="utf-8")):
        if r["label"] is not None:
            d[(r["review_id"] + 1, r["construct"])] = int(r["label"])  # Exp3 sample_id is 0-based
    pred[name] = d


def pairs(m, c, rids):
    y, p = [], []
    for r in rids:
        if gold[(r, c)] is not None and (r, c) in pred[m]:
            y.append(gold[(r, c)]); p.append(pred[m][(r, c)])
    return np.array(y), np.array(p)


def met(y, p):
    k = cohen_kappa_score(y, p) if len(set(y) | set(p)) > 1 else np.nan
    return {"kappa": k, "acc": float((y == p).mean()), "f1": f1_score(y, p, zero_division=0) if (y.sum() + p.sum()) else np.nan,
            "prec": precision_score(y, p, zero_division=0) if p.sum() else np.nan, "rec": recall_score(y, p, zero_division=0) if y.sum() else np.nan}


rng = random.Random(SEED)
boots = [[rng.choice(RIDS) for _ in RIDS] for _ in range(B)]
CS6 = [c for c in C if c != "Change"]
res = {}
for m in MODELS:
    for c in C + ["Macro (6, excl. Change)"]:
        cs = CS6 if c.startswith("Macro") else [c]
        pt = {k: np.nanmean([met(*pairs(m, x, RIDS))[k] for x in cs]) for k in ("kappa", "acc", "f1", "prec", "rec")}
        bk, ba = [], []
        for br in boots:
            ms = [met(*pairs(m, x, br)) for x in cs]
            kk = [x["kappa"] for x in ms]
            bk.append(np.nan if all(np.isnan(kk)) else np.nanmean(kk)); ba.append(np.mean([x["acc"] for x in ms]))
        y, p = pairs(m, cs[0], RIDS)
        res[f"{m}|{c}"] = {**{k: float(v) for k, v in pt.items()},
                           "kappa_ci": [float(np.nanpercentile(bk, 2.5)), float(np.nanpercentile(bk, 97.5))],
                           "acc_ci": [float(np.percentile(ba, 2.5)), float(np.percentile(ba, 97.5))],
                           "undefined_boot": int(np.isnan(bk).sum()), "n": int(len(y)),
                           "model_pos": int(p.sum()) if len(cs) == 1 else None, "human_pos": int(y.sum()) if len(cs) == 1 else None,
                           "_bk": bk}
# pairwise: which model is best? bootstrap P(model A macro kappa > model B)
names = list(MODELS)
rank = {}
for a in names:
    for b in names:
        if a < b:
            da = np.array(res[f"{a}|Macro (6, excl. Change)"]["_bk"]) - np.array(res[f"{b}|Macro (6, excl. Change)"]["_bk"])
            rank[f"{a} - {b}"] = [float(np.mean(da)), float(np.percentile(da, 2.5)), float(np.percentile(da, 97.5)), float(np.mean(da > 0))]
for v in res.values():
    v.pop("_bk")
prev = {c: [sum(1 for r in RIDS if gold[(r, c)] == 1), sum(1 for r in RIDS if gold[(r, c)] is not None)] for c in C}
res = {k: {kk: (None if isinstance(vv, float) and np.isnan(vv) else vv) for kk, vv in v.items()} for k, v in res.items()}
json.dump({"results": res, "pairwise_macro_kappa_diff": rank, "human_prevalence": prev, "B": B, "seed": SEED},
          open(OUT / "exp3_vs_human.json", "w"), indent=1)

# figure: kappa with CIs
cols = {"GPT-4o": "#C55A11", "Sonnet 5.5": "#7F7F7F", "Qwen3-14B": "#1F3864", "Gemma 3 12B": "#BF9000"}
cs = C + ["Macro (6, excl. Change)"]
fig, ax = plt.subplots(figsize=(9, 4.8))
w = 0.2
for j, m in enumerate(names):
    xs = [i + (j - 1.5) * w for i in range(len(cs))]
    ks = [res[f"{m}|{c}"]["kappa"] for c in cs]
    lo = [k - res[f"{m}|{c}"]["kappa_ci"][0] for k, c in zip(ks, cs)]
    hi = [res[f"{m}|{c}"]["kappa_ci"][1] - k for k, c in zip(ks, cs)]
    ax.bar(xs, ks, w, color=cols[m], label=m)
    ax.errorbar(xs, ks, yerr=[lo, hi], fmt="none", ecolor="black", lw=0.7, capsize=1.5)
ax.set_xticks(range(len(cs))); ax.set_xticklabels([c.replace("Absence of ", "").replace(" (6, excl. Change)", "\n(6, excl. Change)") for c in cs], fontsize=8)
ax.axhline(0, color="black", lw=0.6)
for y in (0.2, 0.4, 0.6, 0.8): ax.axhline(y, color="#E0E0E0", lw=0.6, zorder=0)
ax.set_ylabel("Cohen's κ vs human (95% bootstrap CI)"); ax.set_ylim(-0.3, 1.0)
ax.legend(ncol=4, fontsize=8, frameon=False, loc="upper left"); ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.savefig(OUT / "kappa_vs_human.png", dpi=200); plt.close()

# figure: prevalence
fig, ax = plt.subplots(figsize=(9, 3.6))
w = 0.16
for j, (lab, col) in enumerate([("Human", "#2E7D32")] + [(m, cols[m]) for m in names]):
    xs = [i + (j - 2) * w for i in range(len(C))]
    if lab == "Human":
        v = [prev[c][0] / prev[c][1] for c in C]
    else:
        v = [res[f"{lab}|{c}"]["model_pos"] / res[f"{lab}|{c}"]["n"] for c in C]
    ax.bar(xs, v, w, color=col, label=lab)
ax.set_xticks(range(len(C))); ax.set_xticklabels([c.replace("Absence of ", "") for c in C], fontsize=8)
ax.set_ylabel("share coded 1"); ax.legend(ncol=5, fontsize=8, frameon=False); ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.savefig(OUT / "prevalence.png", dpi=200); plt.close()

for c in cs:
    print(c, prev.get(c))
    for m in names:
        r = res[f"{m}|{c}"]
        print(f"   {m:12s} κ {r['kappa']:.3f} [{r['kappa_ci'][0]:.3f},{r['kappa_ci'][1]:.3f}] acc {r['acc']:.2f} F1 {r['f1']:.2f} P {r['prec']:.2f} R {r['rec']:.2f} pos {r['model_pos']} undefined {r['undefined_boot']}")
for k, v in rank.items():
    print(k, [round(x, 3) for x in v])
