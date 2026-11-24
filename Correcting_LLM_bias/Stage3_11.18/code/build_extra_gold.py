"""Add two further human-coded sets to the Stage 3 data:
  Y = Stage1_11.13/random_100_Yuhao.xlsx  (random draw of >25-word reviews, Stage 1; coded with the AI answer visible)
  K = Copy of groupcoding_NR_flipped.xlsx (team group coding, older codebook; NR column already flipped to 'Absence of')
Cleaning: only 0/1 codes kept (other entries such as 9, 10, 'x', '0 but also 1' -> missing); English and > 25 words;
reviews that appear as calibration examples in prompt v2 are dropped (their answers are in the prompt).
book_id / review_id recovered by matching the text in goodreads_reviews_dedup.json; genres joined on book_id.
Writes Stage3/data/stage3_reviews_v2.csv = stage3_reviews.csv + the extra human-coded reviews (with their codes in columns gold: <construct>)."""
import re, json
from pathlib import Path
import orjson, pandas as pd
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0
B = Path(r"C:\Users\gujia\Downloads\books"); S3 = B / "Stage3_11.18"; RAW = B / "RawDataset"
C = ["Absence of Naive Realism", "Theme", "Thought-Provoking", "Ease", "Critic", "Surprise", "Change"]
norm = lambda t: re.sub(r"\s+", " ", str(t)).strip().lower()[:300]
def code(v):
    s = str(v).strip()
    return int(float(s)) if s in ("0", "1", "0.0", "1.0") else None
y = pd.read_excel(B / "Stage1_11.13" / "random_100_Yuhao.xlsx"); k = pd.read_excel(B / "Copy of groupcoding_NR_flipped.xlsx"); k.columns = ["Text"] + C
v2 = re.sub(r"\s+", " ", open(B / "Stage2_11.16/11.16_humanAIcomparasion_finetune/code/prompts_v2.py", encoding="utf-8").read().lower())
rows, log = [], {}
for src, d in (("gold_yuhao", y), ("gold_group", k)):
    d = d[d.Text.notna()]; n0 = len(d); kept = 0; drop = {"<=25 words": 0, "not English": 0, "prompt v2 example": 0}
    for j, r in d.iterrows():
        t = str(r.Text)
        if len(t.split()) <= 25: drop["<=25 words"] += 1; continue
        try: en = detect(t) == "en"
        except Exception: en = False
        if not en: drop["not English"] += 1; continue
        if norm(t)[:60] in v2: drop["prompt v2 example"] += 1; continue
        kept += 1
        rows.append({"unit_id": f"{'Y' if src == 'gold_yuhao' else 'K'}{kept}", "source": src, "review_text": t, "n_words": len(t.split()), "english": True,
                     **{f"gold: {c}": code(r[c]) for c in C}})
    log[src] = {"rows": n0, "kept": kept, **drop}
akey = lambda t: re.sub(r"[^a-z0-9]", "", str(t).lower())[:80]  # robust join key: letters/digits only (formatting differs between files)
X = pd.DataFrame(rows); keys = {akey(t): u for t, u in zip(X.review_text, X.unit_id)}; match = {}
with open(RAW / "※BookReview_Genre_BookID" / "goodreads_reviews_dedup.json", "rb") as f:
    for line in f:
        r = orjson.loads(line); u = keys.get(akey(r["review_text"]))
        if u: match.setdefault(u, []).append((r["review_id"], r["book_id"], r["rating"]))
X["review_id"] = X.unit_id.map(lambda u: match.get(u, [(None,)])[0][0]); X["book_id"] = X.unit_id.map(lambda u: match.get(u, [(None, None)])[0][1])
X["rating"] = X.unit_id.map(lambda u: match.get(u, [(None, None, None)])[0][2]); X["n_matches"] = X.unit_id.map(lambda u: len(match.get(u, [])))
need = set(X.book_id.dropna()); genres = {}
with open(RAW / "BookID_Genres" / "goodreads_book_genres_initial.json", "rb") as f:
    for line in f:
        g = orjson.loads(line)
        if g["book_id"] in need: genres[g["book_id"]] = g["genres"]
base = pd.read_csv(S3 / "data" / "stage3_reviews.csv", encoding="utf-8-sig"); GN = [c for c in base.columns if c.startswith("genre: ") and c != "genre: top"]
for c in GN:
    gname = c[len("genre: "):]; X[c] = X.book_id.map(lambda b: (genres.get(b, {}).get(gname, 0) / sum(genres[b].values())) if b in genres and sum(genres[b].values()) else 0.0)
X["genre: top"] = X.book_id.map(lambda b: max(genres[b], key=genres[b].get) if b in genres and genres[b] else "none")
gold_items = {it["review_id"]: it["labels"] for it in json.load(open(B / "Stage2_11.16/11.16_humanAIcomparasion_finetune/data/dataset.json", encoding="utf-8"))["items"]}
for c in C:
    base[f"gold: {c}"] = base.apply(lambda r: gold_items[int(r.gold_review_id)][c] if r.source == "gold" else None, axis=1)
base["source"] = base.source.replace({"gold": "gold_original"})
out = pd.concat([base, X], ignore_index=True); out.to_csv(S3 / "data" / "stage3_reviews_v2.csv", index=False, encoding="utf-8-sig")
json.dump(log, open(S3 / "outputs" / "extra_gold_log.json", "w"), indent=1)
print(log); print("matched to raw file:", (X.n_matches > 0).sum(), "/", len(X), "| with rating:", X.rating.notna().sum())
print(out.source.value_counts().to_string()); print({c: int(X[f'gold: {c}'].notna().sum()) for c in C})
