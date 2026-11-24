import json
import csv
import random

SOURCE = r"C:\Users\gujia\Downloads\goodreads_reviews_dedup.json\goodreads_reviews_dedup.json"
DEST = r"C:\Users\gujia\Downloads\goodreads_reviews_sample_5000.csv"
K = 5000

FIELDS = [
    "review_id", "user_id", "book_id", "rating", "review_text",
    "date_added", "date_updated", "read_at", "started_at",
    "n_votes", "n_comments",
]

random.seed()
reservoir = []

with open(SOURCE, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        line = line.strip()
        if not line:
            continue

        if i < K:
            reservoir.append(line)
        else:
            j = random.randint(0, i)
            if j < K:
                reservoir[j] = line

        if i % 2_000_000 == 0:
            print(f"...processed {i:,} lines")

print(f"Done streaming. Sampled {len(reservoir)} lines. Writing CSV...")

with open(DEST, "w", encoding="utf-8", newline="") as out:
    writer = csv.DictWriter(out, fieldnames=FIELDS)
    writer.writeheader()
    for line in reservoir:
        record = json.loads(line)
        writer.writerow({field: record.get(field, "") for field in FIELDS})

print(f"Wrote {DEST}")
