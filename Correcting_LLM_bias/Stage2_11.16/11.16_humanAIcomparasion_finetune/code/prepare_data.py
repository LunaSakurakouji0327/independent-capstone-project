"""Read human_coding_100_finished.xlsx -> data/dataset.json with stratified 5-fold assignment."""
import json, random, statistics
from pathlib import Path
import openpyxl

ROOT = Path(__file__).resolve().parents[1]
C = ["Absence of Naive Realism", "Theme", "Thought-Provoking", "Ease", "Critic", "Surprise", "Change"]
K = 5

ws = openpyxl.load_workbook(ROOT / "human_coding_100_finished.xlsx")["Coding"]
hdr = [c.value for c in ws[1]]
col = {h: i + 1 for i, h in enumerate(hdr) if h}
items = []
for r in range(2, ws.max_row + 1):
    text = ws.cell(r, 1).value
    if not text:
        continue
    labels, evidence = {}, {}
    for k, c in enumerate(C):
        v = ws.cell(r, 2 + 2 * k).value
        v = str(v).strip() if v is not None else ""
        labels[c] = int(float(v)) if v in ("0", "1", "0.0", "1.0") else None
        e = ws.cell(r, 3 + 2 * k).value
        evidence[c] = str(e).strip() if e else None
    items.append({"review_id": int(ws.cell(r, col["review_id"]).value), "source_row": int(ws.cell(r, col["source_row (0-based, 5000 file)"]).value),
                  "text": str(text), "labels": labels, "evidence": evidence})

# stratified assignment: search seeds, keep the split whose per-fold positive counts are most even across constructs
def score(assign):
    s = 0
    for c in C:
        per = [sum(1 for it, f in zip(items, assign) if f == k and it["labels"][c] == 1) for k in range(K)]
        s += statistics.pvariance(per) / (statistics.mean(per) + 1)
    return s

best = None
for seed in range(5000):
    rng = random.Random(seed)
    a = [i % K for i in range(len(items))]
    rng.shuffle(a)
    sc = score(a)
    if best is None or sc < best[0]:
        best = (sc, seed, a)
_, seed, assign = best
for it, f in zip(items, assign):
    it["fold"] = f

json.dump({"constructs": C, "folds": K, "split_seed": seed, "items": items}, open(ROOT / "data" / "dataset.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{len(items)} reviews; split seed {seed}")
for c in C:
    per = [sum(1 for it in items if it["fold"] == k and it["labels"][c] == 1) for k in range(K)]
    miss = sum(1 for it in items if it["labels"][c] is None)
    print(f"{c:26s} positives per fold {per}  missing {miss}")
