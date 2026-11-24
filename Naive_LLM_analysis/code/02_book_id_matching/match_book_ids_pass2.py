"""Second pass: validate matches against book genres and resolve unmatched/ambiguous rows.

- Every candidate book's genre set (goodreads_book_genres_initial.json) must equal the
  sample's Genre cell (as a set of ';' combinations).
- Unresolved rows: among the same user's reviews with the same rating and same genre set,
  take the one with the most similar text (difflib ratio >= 0.9, and clearly best).
"""
import json, re, time
from difflib import SequenceMatcher
from collections import defaultdict
import pandas as pd

RAW = r"C:\Users\gujia\Downloads\goodreads_reviews_dedup.json\goodreads_reviews_dedup.json"
GEN = r"C:\Users\gujia\Downloads\books\RawDataset\BookID_Genres\goodreads_book_genres_initial.json"
SAMPLE = r"C:\Users\gujia\Downloads\independent-capstone-project\Naive_LLM_analysis\data\annotated\annotated_50000sample.csv"
MAP = r"C:\Users\gujia\Downloads\independent-capstone-project\Naive_LLM_analysis\data\book_id_mapping\book_id_mapping.csv"
WS = re.compile(r"\s+")
norm = lambda s: WS.sub(" ", str(s)).strip().lower()

df = pd.read_csv(SAMPLE, usecols=["Reviewer ID", "Genre", "Individual review", "Star rating"])
mp = pd.read_csv(MAP, dtype={"book_id": str, "review_id": str})
gset = df["Genre"].map(lambda g: frozenset(x.strip() for x in str(g).split(";") if x.strip()))

genres = {}
with open(GEN, encoding="utf-8") as f:
    for line in f:
        d = json.loads(line)
        genres[d["book_id"]] = frozenset(d["genres"])

# validate existing matches
ok = mp["book_id"].notna()
agree = [genres.get(b) == gset[i] for i, b in zip(mp.index[ok], mp["book_id"][ok])]
print(f"genre agreement on matched rows: {sum(agree):,} / {len(agree):,}")

todo = mp.index[mp["match_type"].isin(["unmatched", "ambiguous"])].tolist()
users = set(df.loc[todo, "Reviewer ID"])
cands = defaultdict(list)
t0 = time.time()
with open(RAW, encoding="utf-8") as f:
    for line in f:
        j = line.find('"user_id": "')
        u = line[j + 12:j + 44]
        if u in users:
            d = json.loads(line)
            cands[u].append((d["book_id"], d["review_id"], d["rating"], norm(d["review_text"])[:1500]))
print(f"pass over raw file: {time.time()-t0:.0f}s")

for i in todo:
    u, sr, gs = df.at[i, "Reviewer ID"], df.at[i, "Star rating"], gset[i]
    t = norm(df.at[i, "Individual review"])[:1500]
    pool = [c for c in cands[u] if c[2] == sr and genres.get(c[0]) == gs]
    scored = sorted(((SequenceMatcher(None, t, c[3], autojunk=False).ratio(), c) for c in pool),
                    key=lambda x: -x[0])
    if scored and scored[0][0] >= 0.9 and (len(scored) == 1 or scored[0][0] - scored[1][0] > 0.05
                                            or scored[0][1][0] == scored[1][1][0]):
        s, c = scored[0]
        mp.loc[i, ["book_id", "review_id", "raw_rating", "match_type"]] = [c[0], c[1], c[2], f"fuzzy_{s:.2f}"]
    elif scored and len({c[0] for s, c in scored if s >= 0.99}) == 1:
        c = scored[0][1]
        mp.loc[i, ["book_id", "review_id", "raw_rating", "match_type"]] = [c[0], c[1], c[2], "genre_disambiguated"]

mp["match_type"] = mp["match_type"].where(~mp["match_type"].str.startswith("fuzzy"), "fuzzy_text>=0.9")
mp.to_csv(MAP, index=False)
print(mp["match_type"].value_counts().to_string())
print("matched total:", mp["book_id"].notna().sum())
