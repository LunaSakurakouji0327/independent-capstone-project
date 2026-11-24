"""Stage 3 analysis: merge labels of 5 models on 150 new reviews; prevalence, pairwise kappa, Fleiss kappa,
prompt (v2/v3/v4) effects, and cost. Writes Stage3/Stage3_results.xlsx and outputs/summary.json."""
import json, itertools, csv
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.metrics import cohen_kappa_score
S3 = Path(r"C:\Users\gujia\Downloads\books\Stage2_11.16\11.17_5modelcomparasion"); O = S3 / "outputs"
C = ["Absence of Naive Realism", "Theme", "Thought-Provoking", "Ease", "Critic", "Surprise", "Change"]; C6 = C[:6]
NAMES = {"sonnet": "Sonnet 5.5", "gemma": "Gemma 3 12B", "qwenft": "Qwen3-14B fine-tuned", "luna": "GPT-6 Luna", "mini": "GPT-5.4 mini"}
PRICE = {"luna": (0.10, 0.01, 0.50), "mini": (0.75, 0.075, 4.50)}  # USD per 1M tokens: input, cached input, output
recs, cost = {}, []
for k in NAMES:
    p = O / f"progress_{k}.jsonl"
    if not p.exists(): continue
    rr = [json.loads(l) for l in open(p, encoding="utf-8")]
    if k == "qwenft":
        for r in rr: recs[(k, r["review_id"], r["construct"])] = (int(r["pred"]), "v1", r["p1"])
        cost.append({"model": NAMES[k], "calls": len(rr), "cost_usd": 0.0, "note": "local GPU"}); continue
    good = [r for r in rr if r["label"] is not None]
    for r in good: recs[(k, r["sample_id"], r["construct"])] = (int(r["label"]), r["prompt"], None)
    if k in PRICE:
        pi, pc, po = PRICE[k]
        inp = sum(r.get("prompt_tokens") or 0 for r in rr); cac = sum(r.get("cached_tokens") or 0 for r in rr)
        out = sum(r.get("completion_tokens") or 0 for r in rr); rea = sum(r.get("reasoning_tokens") or 0 for r in rr)
        usd = ((inp - cac) * pi + cac * pc + out * po) / 1e6
        cost.append({"model": NAMES[k], "calls": len(rr), "input_tokens": inp, "cached_tokens": cac, "output_tokens": out,
                     "reasoning_tokens": rea, "cost_usd": round(usd, 4), "note": f"${pi}/${pc}/${po} per 1M in/cached/out"})
    elif k == "sonnet":
        usd = sum(r.get("cost_usd") or 0 for r in rr)
        disc = O / "discarded_progress_sonnet_heavyCLI.jsonl"
        dusd = sum(json.loads(l).get("cost_usd") or 0 for l in open(disc, encoding="utf-8")) if disc.exists() else 0
        cost.append({"model": NAMES[k], "calls": len(rr), "cost_usd": round(usd, 4),
                     "note": f"API-equivalent (Claude Code CLI total_cost_usd); plus ${dusd:.2f} for 48 discarded calls with the default CLI setup"})
    else:
        cost.append({"model": NAMES[k], "calls": len(rr), "cost_usd": 0.0, "note": "local GPU (Ollama)"})
models = [k for k in NAMES if any(kk[0] == k for kk in recs)]
ids = sorted({kk[1] for kk in recs})
wide = pd.DataFrame([{"sample_id": i, "construct": c, **{NAMES[m]: recs.get((m, i, c), (None,))[0] for m in models},
                      **{f"prompt {NAMES[m]}": recs.get((m, i, c), (None, None))[1] for m in models}} for i in ids for c in C])
prev = pd.DataFrame({NAMES[m]: {c: np.nanmean([recs[(m, i, c)][0] for i in ids if (m, i, c) in recs]) for c in C} for m in models})
pair = []
for a, b in itertools.combinations(models, 2):
    row = {"pair": f"{NAMES[a]} – {NAMES[b]}"}
    for c in C:
        x = [(recs[(a, i, c)][0], recs[(b, i, c)][0]) for i in ids if (a, i, c) in recs and (b, i, c) in recs]
        row[c] = cohen_kappa_score(*zip(*x)) if x and (len({u for u, _ in x}) > 1 or len({v for _, v in x}) > 1) else np.nan
    row["Macro (6, excl. Change)"] = np.nanmean([row[c] for c in C6]); pair.append(row)
pair = pd.DataFrame(pair)
def fleiss(M):
    M = np.asarray(M); n = M.shape[1]; p1 = M.mean(); pe = p1 ** 2 + (1 - p1) ** 2
    s = M.sum(1); P = (s * (s - 1) + (n - s) * (n - s - 1)) / (n * (n - 1)); return (P.mean() - pe) / (1 - pe) if pe < 1 else np.nan
fl = {c: fleiss([[recs[(m, i, c)][0] for m in models] for i in ids if all((m, i, c) in recs for m in models)]) for c in C}
fl["Macro (6, excl. Change)"] = np.nanmean([fl[c] for c in C6])
# prompt effect: per model, share coded 1 and agreement with the majority of the OTHER models, by prompt version
pe = []
for m in models:
    if m == "qwenft": continue
    for v in ["v2", "v3", "v4"]:
        hit, pos, n = 0, 0, 0
        for i in ids:
            for c in C6:
                if (m, i, c) not in recs or recs[(m, i, c)][1] != v: continue
                others = [recs[(o, i, c)][0] for o in models if o != m and (o, i, c) in recs]
                lab = recs[(m, i, c)][0]; pos += lab; n += 1
                if others: hit += int(lab == int(np.mean(others) >= 0.5))
        pe.append({"model": NAMES[m], "prompt": v, "labels": n, "share coded 1": pos / n if n else np.nan, "agreement with majority of other models": hit / n if n else np.nan})
pe = pd.DataFrame(pe)
with pd.ExcelWriter(S3 / "Stage3_results.xlsx") as w:
    pd.DataFrame(cost).to_excel(w, sheet_name="cost", index=False)
    prev.to_excel(w, sheet_name="share coded 1")
    pair.to_excel(w, sheet_name="pairwise kappa", index=False)
    pd.Series(fl, name="Fleiss kappa (all models)").to_excel(w, sheet_name="Fleiss kappa")
    pe.to_excel(w, sheet_name="prompt effect", index=False)
    wide.to_excel(w, sheet_name="labels (long)", index=False)
    for m in models: pd.read_csv(O / f"prompt_assignment_{m}.csv").to_excel(w, sheet_name=f"assign {m}", index=False) if (O / f"prompt_assignment_{m}.csv").exists() else None
json.dump({"cost": cost, "fleiss": fl, "pairwise_macro": dict(zip(pair["pair"], pair["Macro (6, excl. Change)"]))}, open(O / "summary.json", "w"), indent=1, default=float)
pd.set_option("display.width", 200); pd.set_option("display.max_columns", 20)
print(pd.DataFrame(cost)[["model", "calls", "cost_usd"]].to_string(index=False)); print(prev.round(2).to_string())
print(pair[["pair", "Macro (6, excl. Change)"]].round(3).to_string(index=False)); print({k: round(v, 3) for k, v in fl.items()})
print(pe.round(3).to_string(index=False))
