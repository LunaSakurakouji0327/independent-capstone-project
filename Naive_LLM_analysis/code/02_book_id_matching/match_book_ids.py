"""Align the 50k annotated reviews with goodreads_reviews_dedup.json to get book_id / review_id.

Match key: user_id == Reviewer ID  AND  whitespace-normalised review_text == Individual review.
Fallback for reviews whose text differs slightly (e.g. truncation / cleaning): same user and the
first 200 normalised characters match, provided that is unique for that user.
"""
import json, re, sys, time
from collections import defaultdict
import pandas as pd

RAW = r"C:\Users\gujia\Downloads\goodreads_reviews_dedup.json\goodreads_reviews_dedup.json"
SAMPLE = r"C:\Users\gujia\Downloads\independent-capstone-project\Naive_LLM_analysis\data\annotated\annotated_50000sample.csv"
OUT = r"C:\Users\gujia\Downloads\independent-capstone-project\Naive_LLM_analysis\data\book_id_mapping\book_id_mapping.csv"
WS = re.compile(r"\s+")
norm = lambda s: WS.sub(" ", str(s)).strip().lower()

df = pd.read_csv(SAMPLE, usecols=["Reviewer ID", "Individual review", "Star rating"])
users = set(df["Reviewer ID"])
full_key = defaultdict(list)    # (user, full text) -> rows
pref_key = defaultdict(list)    # (user, prefix)    -> rows
for i, (u, t) in enumerate(zip(df["Reviewer ID"], df["Individual review"])):
    n = norm(t)
    full_key[(u, n)].append(i)
    pref_key[(u, n[:200])].append(i)

full_hits, pref_hits = {}, defaultdict(list)
t0 = time.time()
with open(RAW, encoding="utf-8") as f:
    for ln, line in enumerate(f, 1):
        # lines start with {"user_id": "<32 hex>", ...  -> cheap pre-filter
        j = line.find('"user_id": "')
        u = line[j + 12:j + 44]
        if u in users:
            d = json.loads(line)
            n = norm(d["review_text"])
            rec = (d["book_id"], d["review_id"], d["rating"])
            for r in full_key.get((u, n), []):
                full_hits.setdefault(r, []).append(rec)
            for r in pref_key.get((u, n[:200]), []):
                pref_hits[r].append(rec)
        if ln % 2_000_000 == 0:
            print(f"{ln:,} lines, {time.time()-t0:.0f}s, full matches {len(full_hits):,}", flush=True)

rows = []
for i in range(len(df)):
    cands, how = full_hits.get(i, []), "exact_text"
    if not cands:
        cands, how = pref_hits.get(i, []), "prefix200"
    uniq = {c[0] for c in cands}
    if len(uniq) == 1:
        b, rid, rt = cands[0]
        rows.append((i, b, rid, rt, how))
    elif len(uniq) > 1:
        # several books: prefer the one whose rating equals the star rating
        sr = df["Star rating"].iat[i]
        c2 = [c for c in cands if c[2] == sr]
        if len({c[0] for c in c2}) == 1:
            rows.append((i, c2[0][0], c2[0][1], c2[0][2], how + "+rating"))
        else:
            rows.append((i, None, None, None, "ambiguous"))
    else:
        rows.append((i, None, None, None, "unmatched"))

out = pd.DataFrame(rows, columns=["row", "book_id", "review_id", "raw_rating", "match_type"])
out.to_csv(OUT, index=False)
print(out["match_type"].value_counts().to_string())
print("rating agrees:", (out["raw_rating"] == df["Star rating"]).sum(), "of", out["raw_rating"].notna().sum())
print(f"done in {time.time()-t0:.0f}s")
