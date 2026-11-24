"""Stage 3 dataset: 2,900 new English reviews (> 25 words) + the 100 human-coded (gold) reviews, with book_id and genres.
One pass over goodreads_reviews_dedup.json (15.7M reviews, the population the 5000-review sample was drawn from):
  * gold reviews are matched by text to recover review_id / book_id (SQL-like join on review content);
  * a reservoir of 40,000 reviews with > 25 words is drawn, excluding every review in the 5000-review pool and every review
    used before (human coding sets, random_100, 150-review sample); English is then checked with langdetect and 2,900 kept.
Genres from goodreads_book_genres_initial.json are joined on book_id (vote shares per genre).
Writes Stage3/data/stage3_reviews.csv (unit_id, source, gold_review_id, review_id, book_id, rating, n_words, review_text, genre shares...)."""
import re, json, random, csv, time
from pathlib import Path
import orjson, pandas as pd
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0
B = Path(r"C:\Users\gujia\Downloads\books"); RAW = B / "RawDataset"; S3 = B / "Stage3_11.18"; (S3 / "data").mkdir(exist_ok=True)
DEDUP = RAW / "※BookReview_Genre_BookID" / "goodreads_reviews_dedup.json"; GEN = RAW / "BookID_Genres" / "goodreads_book_genres_initial.json"
F = B / "Stage2_11.16" / "11.16_humanAIcomparasion_finetune"
norm = lambda t: re.sub(r"\s+", " ", str(t)).strip().lower()[:300]
gold = json.load(open(F / "data" / "dataset.json", encoding="utf-8"))["items"]
gold_key = {norm(it["text"]): it["review_id"] for it in gold}
used = set(gold_key)
used |= {norm(t) for t in pd.read_csv(B / "Stage1_11.13" / "goodreads_reviews_5000_annotated.csv", encoding="utf-8").review_text.dropna()}
for f, col in [("Stage2_11.16/human_coding_200.xlsx", "Review"), ("Stage2_11.16/human_coding_100_finished.xlsx", "Review"), ("random_100.xlsx", "Text")]:
    used |= {norm(t) for t in pd.read_excel(B / f)[col].dropna()}
used |= {norm(t) for t in pd.read_csv(B / "Stage2_11.16" / "11.17_5modelcomparasion" / "sample_150.csv", encoding="utf-8-sig").review_text}
print("excluded texts:", len(used), flush=True)
rng = random.Random(20261117); K = 40000; res = []; seen = 0; matches = {}
t0 = time.time()
with open(DEDUP, "rb") as f:
    for n, line in enumerate(f):
        r = orjson.loads(line); txt = r["review_text"]; k = norm(txt)
        if k in gold_key: matches.setdefault(gold_key[k], []).append((r["review_id"], r["book_id"], r["rating"]))
        if k in used or len(txt.split()) <= 25: continue
        seen += 1
        if len(res) < K: res.append(r)
        else:
            j = rng.randrange(seen)
            if j < K: res[j] = r
        if n % 2_000_000 == 0: print(f"{n:,} lines, {time.time() - t0:.0f}s", flush=True)
print(f"done: {n + 1:,} lines, eligible (>25 words, unused) {seen:,}; gold matched {len(matches)}/100", flush=True)
rng.shuffle(res); new = []
for r in res:
    try:
        if detect(r["review_text"]) == "en": new.append(r)
    except Exception: pass
    if len(new) == 2900: break
print("new English reviews:", len(new), flush=True)
need = {r["book_id"] for r in new} | {m[0][1] for m in matches.values()}
genres = {}
with open(GEN, "rb") as f:
    for line in f:
        g = orjson.loads(line)
        if g["book_id"] in need: genres[g["book_id"]] = g["genres"]
GN = sorted({k for g in genres.values() for k in g})
def gshare(bid):
    g = genres.get(bid, {}); s = sum(g.values())
    return {f"genre: {k}": (g.get(k, 0) / s if s else 0.0) for k in GN} | {"genre: top": (max(g, key=g.get) if g else "none")}
rows = []
for it in gold:
    m = matches.get(it["review_id"], [])
    rid, bid, rat = (m[0] if m else (None, None, None))
    rows.append({"unit_id": f"G{it['review_id']}", "source": "gold", "gold_review_id": it["review_id"], "review_id": rid, "book_id": bid, "rating": rat,
                 "n_matches": len(m), "n_words": len(it["text"].split()), "english": (lambda t: (lambda: detect(t) == "en")())(it["text"]),
                 "review_text": it["text"], **gshare(bid)})
for j, r in enumerate(new, 1):
    rows.append({"unit_id": f"N{j}", "source": "new", "gold_review_id": None, "review_id": r["review_id"], "book_id": r["book_id"], "rating": r["rating"],
                 "n_matches": 1, "n_words": len(r["review_text"].split()), "english": True, "review_text": r["review_text"], **gshare(r["book_id"])})
df = pd.DataFrame(rows); df.to_csv(S3 / "data" / "stage3_reviews.csv", index=False, encoding="utf-8-sig")
g = df[df.source == "gold"]
print("gold: matched", (g.n_matches > 0).sum(), "| ambiguous (>1 match)", (g.n_matches > 1).sum(), "| >25 words", (g.n_words > 25).sum(), "| English", g.english.sum())
print("genre coverage:", (df["genre: top"] != "none").mean().round(3)); print(df["genre: top"].value_counts().to_string())
