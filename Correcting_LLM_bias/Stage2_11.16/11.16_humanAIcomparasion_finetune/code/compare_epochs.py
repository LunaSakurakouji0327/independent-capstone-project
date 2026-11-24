"""Paired bootstrap (500, seed 2026) of macro kappa: 1-epoch vs 2-epoch 5-fold CV predictions."""
import json, numpy as np
from sklearn.metrics import cohen_kappa_score
C6 = ["Absence of Naive Realism", "Theme", "Thought-Provoking", "Ease", "Critic", "Surprise"]
def load(p): return {(r["review_id"], r["construct"]): r for r in map(json.loads, open(p, encoding="utf-8")) if r["gold"] is not None}
e2, e1 = load("outputs/predictions_finetuned.jsonl"), load("outputs_1epoch/predictions_finetuned.jsonl")
ids = sorted({k[0] for k in e2})
def stats(sample):
    out = {}
    for name, P in (("2ep", e2), ("1ep", e1)):
        ks, accs = [], []
        for c in C6:
            g = [P[(i, c)]["gold"] for i in sample if (i, c) in P]; p = [P[(i, c)]["pred"] for i in sample if (i, c) in P]
            k = cohen_kappa_score(g, p) if len(set(g)) > 1 or len(set(p)) > 1 else np.nan
            ks.append(k); accs += [a == b for a, b in zip(g, p)]
        out[name] = (np.nanmean(ks), np.mean(accs), ks)
    return out
full = stats(ids)
rng = np.random.default_rng(2026); d = []
for _ in range(500):
    s = stats(list(rng.choice(ids, len(ids)))); d.append(s["1ep"][0] - s["2ep"][0])
d = np.array(d)
res = {"macro_kappa_2ep": full["2ep"][0], "macro_kappa_1ep": full["1ep"][0], "acc_2ep": full["2ep"][1], "acc_1ep": full["1ep"][1],
       "per_construct_kappa_2ep": dict(zip(C6, full["2ep"][2])), "per_construct_kappa_1ep": dict(zip(C6, full["1ep"][2])),
       "diff_1ep_minus_2ep": [float(np.mean(d)), float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5)), float(np.mean(d > 0))]}
json.dump(res, open("outputs_1epoch/epoch_comparison.json", "w"), indent=1)
print(json.dumps(res, indent=1))
