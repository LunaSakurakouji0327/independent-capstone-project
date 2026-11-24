"""Pairwise agreement (accuracy, F1 on class 1, Cohen's kappa) among Human, GPT-4o, GPT-6-Luna on the 100 gold reviews,
prompt v1. Per construct + macro (6 constructs excl. Change, and all 7); 500 review-level bootstrap 95% CIs for macro."""
import json, random
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.metrics import cohen_kappa_score, f1_score
S2 = Path(r"C:\Users\gujia\Downloads\books\Stage2_11.16"); D = S2 / "11.19_v1_4o_luna"
data = json.load(open(S2 / "11.16_humanAIcomparasion_finetune/data/dataset.json", encoding="utf-8"))
C = data["constructs"]; RIDS = [it["review_id"] for it in data["items"]]
L = {"Human": {(it["review_id"], c): it["labels"][c] for it in data["items"] for c in C}}
for name, k in (("GPT-4o", "4o"), ("GPT-6-Luna", "luna")):
    L[name] = {(r["review_id"], r["construct"]): r["label"] for r in map(json.loads, open(D / f"outputs/labels_{k}.jsonl", encoding="utf-8"))}
PAIRS = [("GPT-4o", "Human"), ("GPT-6-Luna", "Human"), ("GPT-4o", "GPT-6-Luna")]

def met(a, b, c, rids):
    x = [(L[a][(r, c)], L[b][(r, c)]) for r in rids if L[a].get((r, c)) is not None and L[b].get((r, c)) is not None]
    p, y = np.array(x).T
    k = cohen_kappa_score(y, p) if len(set(y) | set(p)) > 1 else np.nan
    return {"acc": float((y == p).mean()), "f1": f1_score(y, p, zero_division=0) if y.sum() + p.sum() else np.nan, "kappa": k,
            "n": len(y), f"{a}_pos": int(p.sum()), f"{b}_pos": int(y.sum())}

rows = []
rng = random.Random(2026); boots = [[rng.choice(RIDS) for _ in RIDS] for _ in range(500)]
for a, b in PAIRS:
    for c in C:
        m = met(a, b, c, RIDS); rows.append({"pair": f"{a} vs {b}", "construct": c, "acc": m["acc"], "f1": m["f1"], "kappa": m["kappa"],
                                            "n": m["n"], "pos_A": m[f"{a}_pos"], "pos_B": m[f"{b}_pos"]})
    for tag, cs in (("Macro (6, excl. Change)", [c for c in C if c != "Change"]), ("Macro (all 7)", C)):
        pt = {k: np.nanmean([met(a, b, c, RIDS)[k] for c in cs]) for k in ("acc", "f1", "kappa")}
        bs = {k: [] for k in pt}
        for br in boots:
            ms = [met(a, b, c, br) for c in cs]
            for k in bs: bs[k].append(np.nanmean([m[k] for m in ms]))
        rows.append({"pair": f"{a} vs {b}", "construct": tag, **pt,
                     **{f"{k}_ci": f"[{np.nanpercentile(v, 2.5):.3f}, {np.nanpercentile(v, 97.5):.3f}]" for k, v in bs.items()}})
df = pd.DataFrame(rows)
df.to_excel(D / "v1_4o_luna_human_comparison.xlsx", sheet_name="metrics", index=False)
# predictions sheet for inspection
pred = pd.DataFrame([{"review_id": r, "construct": c, **{n: L[n].get((r, c)) for n in L}} for r in RIDS for c in C])
with pd.ExcelWriter(D / "v1_4o_luna_human_comparison.xlsx", mode="a", engine="openpyxl") as w: pred.to_excel(w, sheet_name="labels", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 20)
print(df.round(3).to_string(index=False))
