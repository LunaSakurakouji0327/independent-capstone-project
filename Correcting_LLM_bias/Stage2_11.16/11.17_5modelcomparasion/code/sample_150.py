"""Draw 150 new English reviews from the Stage 1 5000-review pool, excluding every review used before."""
import re, pandas as pd
from pathlib import Path
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0
B = Path(r"C:\Users\gujia\Downloads\books")
pool = pd.read_csv(B / "Stage1_11.13" / "goodreads_reviews_5000_annotated.csv", encoding="utf-8")
norm = lambda t: re.sub(r"\s+", " ", str(t)).strip().lower()[:300]
used = set()
for f, col in [("Stage2_11.16/human_coding_200.xlsx", "Review"), ("Stage2_11.16/human_coding_100_finished.xlsx", "Review"),
               ("random_100.xlsx", "Text")]:
    used |= {norm(t) for t in pd.read_excel(B / f)[col]}
for f in [r"C:\Users\gujia\AppData\Local\Temp\gr_ann_5f086d5034\compare120_v2\sample_120_v2.csv",
          r"C:\Users\gujia\AppData\Local\Temp\gr_ann_5f086d5034\compare120_v2\sample_200_human.csv"]:
    if Path(f).exists():
        d = pd.read_csv(f, encoding="utf-8-sig"); used |= {norm(t) for t in d[[c for c in d.columns if "text" in c.lower() or c == "Review"][0]]}
pool["source_row"] = pool.index
pool = pool[pool.review_text.notna()]
pool = pool[~pool.review_text.map(norm).isin(used)]
pool = pool[pool.review_text.str.split().str.len() >= 10]
def en(t):
    try: return detect(t) == "en"
    except Exception: return False
pool = pool[pool.review_text.map(en)]
print("eligible:", len(pool), "| excluded as used:", len(used))
s = pool.sample(150, random_state=20261117).reset_index(drop=True)
s.insert(0, "sample_id", range(1, 151))
s[["sample_id", "source_row", "rating", "review_text"]].to_csv(B / "Stage2_11.16" / "11.17_5modelcomparasion" / "sample_150.csv", index=False, encoding="utf-8-sig")
print("wrote Stage3/sample_150.csv")
