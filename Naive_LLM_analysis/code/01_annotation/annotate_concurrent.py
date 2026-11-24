"""
Concurrent GPT-4o annotation using the v1 prompts from llm_content_analysis_script.ipynb.

- Prompts are loaded verbatim from the notebook (cell containing `prompts = {`).
- Same request as the notebook: model gpt-4o, same system message, temperature=0.
- Every (row, dimension) result is stored immediately in a SQLite file, so the run can
  be stopped (Ctrl+C) and restarted at any time without losing or repeating work.
- Existing valid answers from the old checkpoint xlsx are imported first (not re-run).

Usage (PowerShell):
  $env:OPENAI_API_KEY = "sk-..."
  python annotate_concurrent.py --scope sample      # finish the 50k checkpoint sample
  python annotate_concurrent.py --scope full        # annotate the full 1.14M dataset
  python annotate_concurrent.py --scope sample --export-only   # just write output files
"""
import argparse, asyncio, json, os, random, sqlite3, sys, time
from pathlib import Path

import pandas as pd
from openai import AsyncOpenAI
import openai

DL = Path(r"C:\Users\gujia\Downloads")
NOTEBOOK = DL / "llm_content_analysis_script.ipynb"
CHECKPOINT = DL / "annotation_checkpoint.xlsx"
FULL = DL / "Final_Goodreads_dataset.csv"
RUN_DIR = Path(__file__).resolve().parents[2]   # project root (Naive_LLM_analysis)
KEY = ["Reviewer ID", "Title of the book", "Individual review"]
TEXT_COL = "Individual review"
SYSTEM_MSG = "You are the expert in content analysis of book review."
MODEL = "gpt-4o"


def load_prompts():
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    for c in nb["cells"]:
        src = "".join(c["source"])
        if "prompts = {" in src:
            ns = {}
            exec(src, ns)
            return ns["prompts"]
    raise RuntimeError("prompts cell not found in notebook")


def valid(ans):
    return isinstance(ans, str) and ans.strip() in ("0", "1")


def init_db(path):
    con = sqlite3.connect(path)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("""CREATE TABLE IF NOT EXISTS results(
        row_id INTEGER, dim TEXT, answer TEXT, in_tok INTEGER, out_tok INTEGER,
        PRIMARY KEY(row_id, dim))""")
    con.commit()
    return con


def load_data(scope):
    if scope == "sample":
        df = pd.read_excel(CHECKPOINT)
        old = df  # old answers live in the same frame
    else:
        df = pd.read_csv(FULL)
        ck = pd.read_excel(CHECKPOINT).drop_duplicates(KEY)
        ck = ck[KEY + [c for c in ck.columns if c.endswith("_AI")]]
        old = df[KEY].merge(ck, on=KEY, how="left")  # left merge, unique right keys -> same order
        assert len(old) == len(df)
    df = df.reset_index(drop=True)
    old = old.reset_index(drop=True)
    return df, old


def import_old(con, df, old, prompts):
    n = 0
    rows = []
    for dim in prompts:
        col = f"{dim}_AI"
        if col not in old.columns:
            continue
        s = old[col]
        for rid, v in s.items():
            if pd.isna(v):
                continue
            v = str(int(v)) if isinstance(v, float) else str(v).strip()
            if valid(v):
                rows.append((int(rid), dim, v, None, None))
    con.executemany("INSERT OR IGNORE INTO results VALUES (?,?,?,?,?)", rows)
    con.commit()
    return len(rows)


class Limiter:
    """Shared back-off: when any request hits a 429, all workers pause briefly."""
    def __init__(self):
        self.until = 0.0

    async def wait(self):
        d = self.until - time.monotonic()
        if d > 0:
            await asyncio.sleep(d)

    def hit(self, secs):
        self.until = max(self.until, time.monotonic() + secs)


async def worker(name, q, client, prompts, texts, results_q, lim, stats, max_retries):
    while True:
        item = await q.get()
        if item is None:
            q.task_done()
            return
        rid, dim = item
        prompt = prompts[dim].format(text=texts[rid])
        ans, it, ot = None, 0, 0
        for attempt in range(max_retries):
            await lim.wait()
            try:
                r = await client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "system", "content": SYSTEM_MSG},
                              {"role": "user", "content": prompt}],
                    temperature=0,
                )
                ans = r.choices[0].message.content.strip()
                it, ot = r.usage.prompt_tokens, r.usage.completion_tokens
                break
            except openai.RateLimitError as e:
                stats["429"] += 1
                if "insufficient_quota" in str(e):
                    print("\n!!! insufficient_quota: account out of credit. Stopping.", flush=True)
                    stats["fatal"] = True
                    break
                lim.hit(min(60, 2 ** attempt) + random.random())
            except (openai.BadRequestError,) as e:
                # e.g. content filter / invalid input: record so it is not retried forever
                ans = f"ERROR: {str(e)[:200]}"
                break
            except Exception as e:  # timeouts, 5xx, connection errors
                stats["err"] += 1
                await asyncio.sleep(min(60, 2 ** attempt) + random.random())
        if ans is not None:
            await results_q.put((rid, dim, ans, it, ot))
        else:
            stats["failed"] += 1
        q.task_done()


async def writer(con, results_q, stats, total, t0):
    buf, last_flush, last_print = [], time.monotonic(), 0
    while True:
        item = await results_q.get()
        if item is None:
            break
        buf.append(item)
        stats["done"] += 1
        stats["in_tok"] += item[3]
        stats["out_tok"] += item[4]
        now = time.monotonic()
        if len(buf) >= 500 or now - last_flush > 5:
            con.executemany("INSERT OR REPLACE INTO results VALUES (?,?,?,?,?)", buf)
            con.commit()
            buf, last_flush = [], now
        if now - last_print > 10:
            last_print = now
            el = now - t0
            rate = stats["done"] / el if el else 0
            eta = (total - stats["done"]) / rate / 3600 if rate else float("inf")
            cost = stats["in_tok"] * 2.5e-6 + stats["out_tok"] * 10e-6
            print(f"[{time.strftime('%H:%M:%S')}] {stats['done']:,}/{total:,} "
                  f"| {rate*60:,.0f}/min | ETA {eta:.2f}h | cost ${cost:,.2f} "
                  f"| 429s {stats['429']} errs {stats['err']} failed {stats['failed']}",
                  flush=True)
    if buf:
        con.executemany("INSERT OR REPLACE INTO results VALUES (?,?,?,?,?)", buf)
        con.commit()


async def run(args, df, prompts, con):
    done = set(con.execute("SELECT row_id, dim FROM results WHERE answer IN ('0','1')"))
    todo = [(rid, dim) for dim in prompts for rid in range(len(df)) if (rid, dim) not in done]
    if args.limit:
        todo = todo[: args.limit]
    print(f"Already done: {len(done):,} | to do now: {len(todo):,}", flush=True)
    if not todo:
        return
    texts = df[TEXT_COL].tolist()  # notebook used str.format on the raw value (NaN -> 'nan')
    client = AsyncOpenAI(max_retries=0, timeout=60)
    q = asyncio.Queue(maxsize=args.concurrency * 4)
    results_q = asyncio.Queue()
    lim = Limiter()
    stats = dict(done=0, in_tok=0, out_tok=0, err=0, failed=0, fatal=False, **{"429": 0})
    t0 = time.monotonic()
    w = asyncio.create_task(writer(con, results_q, stats, len(todo), t0))
    workers = [asyncio.create_task(worker(i, q, client, prompts, texts, results_q, lim, stats,
                                          args.max_retries)) for i in range(args.concurrency)]
    try:
        for item in todo:
            if stats["fatal"]:
                break
            await q.put(item)
    finally:
        for _ in workers:
            await q.put(None)
        await asyncio.gather(*workers)
        await results_q.put(None)
        await w
    cost = stats["in_tok"] * 2.5e-6 + stats["out_tok"] * 10e-6
    print(f"Finished this pass: {stats['done']:,} results, {stats['failed']} failed, "
          f"{(time.monotonic()-t0)/3600:.2f}h, ${cost:,.2f}", flush=True)


def export(df, prompts, con, scope):
    res = pd.read_sql("SELECT row_id, dim, answer FROM results", con)
    wide = res.pivot(index="row_id", columns="dim", values="answer")
    out = df[[c for c in df.columns if not c.endswith("_AI")]].copy()
    for dim in prompts:
        col = wide[dim] if dim in wide.columns else pd.Series(dtype=object)
        s = out.index.to_series().map(col)
        out[f"{dim}_AI"] = pd.to_numeric(s.where(s.isin(["0", "1"])), errors="coerce").astype("Int64")
        bad = s[s.notna() & ~s.isin(["0", "1"])]
        if len(bad):
            print(f"  {dim}: {len(bad)} non-0/1 answers (left blank; raw text kept in DB)")
    stem = RUN_DIR / "data" / "annotated" / f"annotated_{scope}"
    out.to_csv(f"{stem}.csv", index=False, encoding="utf-8-sig")
    if len(out) < 1_048_000:
        out.to_excel(f"{stem}.xlsx", index=False)
    print("Exported:", f"{stem}.csv", "(+ .xlsx)" if len(out) < 1_048_000 else "")
    print(out[[f"{d}_AI" for d in prompts]].notna().sum().to_string())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", choices=["sample", "full"], required=True)
    ap.add_argument("--concurrency", type=int, default=64)
    ap.add_argument("--max-retries", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0, help="only run N requests (for testing)")
    ap.add_argument("--export-only", action="store_true")
    args = ap.parse_args()

    prompts = load_prompts()
    print("Dimensions:", list(prompts))
    df, old = load_data(args.scope)
    print(f"Rows: {len(df):,}")
    con = init_db(RUN_DIR / "cache" / f"results_{args.scope}.sqlite")
    print("Imported valid old answers:", import_old(con, df, old, prompts))
    if not args.export_only:
        keyfile = DL / ".openai_key.txt"
        if not os.environ.get("OPENAI_API_KEY") and keyfile.exists():
            os.environ["OPENAI_API_KEY"] = keyfile.read_text(encoding="utf-8-sig").strip()
        if not os.environ.get("OPENAI_API_KEY"):
            try:  # key set via `setx` is in the registry but not in already-running shells
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
                    os.environ["OPENAI_API_KEY"] = winreg.QueryValueEx(k, "OPENAI_API_KEY")[0]
            except OSError:
                pass
        if not os.environ.get("OPENAI_API_KEY"):
            sys.exit("Set OPENAI_API_KEY first.")
        try:
            asyncio.run(run(args, df, prompts, con))
        except KeyboardInterrupt:
            print("Interrupted; progress is saved in the SQLite file.")
    export(df, prompts, con, args.scope)


if __name__ == "__main__":
    main()
