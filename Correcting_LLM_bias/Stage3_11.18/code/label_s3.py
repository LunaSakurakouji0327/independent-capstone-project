"""Usage: python label_s3.py <luna|mini|gemma|sonnet> [goldfill]
Labels the 2,900 new Stage 3 reviews x 7 constructs with the Latin-square prompt design (same as Stage 2 Step 7):
on every review Sonnet, Gemma and the GPT group (Luna + 5.4 mini) get three different prompts among v2/v3/v4; the six
orderings are used equally often and assigned at random (data/latin_assignment.csv). Resumable: outputs/progress_<model>.jsonl.
goldfill: on the 100 gold reviews, cells skipped in Stage 2 because the review is a calibration example of the assigned prompt
are labelled with the example-free prompt v2 (outputs/goldfill_<model>.jsonl)."""
import os, sys, csv, json, re, time, random, subprocess, threading, itertools, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
B = Path(r"C:\Users\gujia\Downloads\books"); S3 = B / "Stage3_11.18"; OUT = S3 / "outputs"; S2 = B / "Stage2_11.16" / "11.17_5modelcomparasion"
def load(p):
    ns = {}; exec(open(p, encoding="utf-8").read(), ns); return ns
PROMPTS = {"v2": load(B / "Stage2_11.16/11.16_humanAIcomparasion_finetune/code/prompts_v2.py")["prompts"],
           "v3": load(B / "prompts_v3.py")["prompts"], "v4": load(B / "prompts_v4.py")["prompts"]}
EXAMPLES = {"v3": load(B / "prompts_v3.py")["EXAMPLE_IDS"], "v4": load(B / "prompts_v4.py")["EXAMPLE_IDS"]}
CONSTRUCTS = ["Absence of Naive Realism", "Theme", "Thought-Provoking", "Ease", "Critic", "Surprise", "Change"]
LABEL_RE = re.compile(r"^[01]$"); QUOTA_RE = re.compile(r"hit your.*limit|usage limit|insufficient_quota", re.I)
key = sys.argv[1]; GOLDFILL = "goldfill" in sys.argv[2:]; EXTRA = "extragold" in sys.argv[2:]  # extragold: Yuhao + group-coded reviews
MODEL = {"sonnet": "claude-sonnet-5-5", "gemma": "gemma3:12b", "luna": "gpt-6-luna", "mini": "gpt-5.4-mini"}[key]
GRP = {"sonnet": "sonnet", "gemma": "gemma", "luna": "gpt", "mini": "gpt"}[key]
stop = threading.Event()
# Latin-square assignment for the new reviews (created once, shared by all models)
rows = [r for r in csv.DictReader(open(S3 / "data" / "stage3_reviews.csv", encoding="utf-8-sig")) if r["source"] == "new"]
LA = S3 / "data" / "latin_assignment.csv"
if not LA.exists():
    perms = list(itertools.permutations(["v2", "v3", "v4"])); rng = random.Random(33)
    seq = [perms[i % 6] for i in range(len(rows))]; rng.shuffle(seq)
    with open(LA, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["unit_id", "sonnet", "gemma", "gpt"]); [w.writerow([r["unit_id"], *p]) for r, p in zip(rows, seq)]
ASSIGN = {r["unit_id"]: r[GRP] for r in csv.DictReader(open(LA))}
if EXTRA:
    rows = [r for r in csv.DictReader(open(S3 / "data" / "stage3_reviews_v2.csv", encoding="utf-8-sig")) if r["source"] in ("gold_yuhao", "gold_group")]
    LAX = S3 / "data" / "latin_assignment_extra.csv"
    if not LAX.exists():
        perms = list(itertools.permutations(["v2", "v3", "v4"])); rng = random.Random(34); seq = [perms[i % 6] for i in range(len(rows))]; rng.shuffle(seq)
        with open(LAX, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["unit_id", "sonnet", "gemma", "gpt"]); [w.writerow([r["unit_id"], *p]) for r, p in zip(rows, seq)]
    ASSIGN = {r["unit_id"]: r[GRP] for r in csv.DictReader(open(LAX))}
if GOLDFILL:
    ds = json.load(open(B / "Stage2_11.16/11.16_humanAIcomparasion_finetune/data/dataset.json", encoding="utf-8"))["items"]
    ga = {int(r["sample_id"]): r[GRP] for r in csv.DictReader(open(S2 / "outputs" / "latin_assignment_gold.csv"))}
    rows = [{"unit_id": f"G{it['review_id']}", "review_text": it["text"], "_c": c} for it in ds for c in CONSTRUCTS
            if it["review_id"] in EXAMPLES.get(ga[it["review_id"]], {}).get(c, [])]
    ASSIGN = {r["unit_id"]: "v2" for r in rows}
PROGRESS = OUT / (f"goldfill_{key}.jsonl" if GOLDFILL else f"extragold_{key}.jsonl" if EXTRA else f"progress_{key}.jsonl")

def parse(out):
    out = re.sub(r"<think>.*?</think>", "", out or "", flags=re.S).strip()
    c = [x for x in (ln.strip().strip("*`. ") for ln in out.splitlines()) if LABEL_RE.match(x)]
    return (c[-1] if c else None), out[:60]

def call_openai(prompt):
    k = open(os.path.expanduser(r"~\.openai_key"), encoding="utf-8").read().strip()
    body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": prompt}], "max_completion_tokens": 2000}).encode()
    err = None
    for a in range(6):
        req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=body, headers={"Content-Type": "application/json", "Authorization": f"Bearer {k}"})
        try: d = json.loads(urllib.request.urlopen(req, timeout=180).read())
        except urllib.error.HTTPError as e:
            err = f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:200]}"
            if e.code in (401, 403, 404) or QUOTA_RE.search(err): stop.set(); return None, err, {}
            time.sleep(2 ** a * 2); continue
        except Exception as e: err = str(e)[:150]; time.sleep(2 ** a); continue
        u = d.get("usage", {}); lab, raw = parse(d["choices"][0]["message"]["content"])
        meta = {"resolved_model": d.get("model"), "prompt_tokens": u.get("prompt_tokens"), "cached_tokens": (u.get("prompt_tokens_details") or {}).get("cached_tokens", 0),
                "completion_tokens": u.get("completion_tokens"), "reasoning_tokens": (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0), "raw": raw}
        return (lab, None, meta) if lab else (None, "unparseable: " + raw, meta)
    return None, err, {}

def call_claude(prompt):
    err = None
    for a in range(3):
        time.sleep(1 + random.random())
        try:
            r = subprocess.run(["cmd", "/c", "claude.cmd", "-p", "--model", MODEL, "--output-format", "json", "--tools", "",
                                "--system-prompt", "You are a careful content-analysis coder. Follow the user's coding instructions exactly and answer with the code only."],
                               input=prompt, capture_output=True, text=True, encoding="utf-8", timeout=180)
        except subprocess.TimeoutExpired: err = "timeout"; continue
        try: d = json.loads(r.stdout)
        except Exception:
            err = (r.stdout + r.stderr)[:200]
            if QUOTA_RE.search(err): stop.set(); return None, err, {}
            time.sleep(3 + 3 * a); continue
        res = str(d.get("result", ""))
        if d.get("is_error") or r.returncode != 0:
            err = res[:200]
            if QUOTA_RE.search(err): stop.set(); return None, err, {}
            time.sleep(3 + 3 * a); continue
        lab, raw = parse(res); meta = {"resolved_model": ",".join(d.get("modelUsage", {}).keys()), "cost_usd": d.get("total_cost_usd"), "raw": raw}
        if lab: return lab, None, meta
        err = "unparseable: " + raw
    return None, err, {}

def call_ollama(prompt):
    body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": prompt}], "stream": False, "options": {"temperature": 0, "num_ctx": 8192, "num_predict": 16}}).encode()
    err = None
    for _ in range(3):
        try:
            req = urllib.request.Request("http://localhost:11434/api/chat", data=body, headers={"Content-Type": "application/json"})
            d = json.loads(urllib.request.urlopen(req, timeout=600).read())
        except Exception as e: err = str(e)[:150]; time.sleep(3); continue
        lab, raw = parse(d["message"]["content"])
        return (lab, None, {"resolved_model": d.get("model"), "raw": raw}) if lab else (None, "unparseable: " + raw, {})
    return None, err, {}

CALL, WORKERS = {"luna": (call_openai, 12), "mini": (call_openai, 12), "sonnet": (call_claude, 6), "gemma": (call_ollama, 1)}[key]
done = set()
if PROGRESS.exists():
    for l in open(PROGRESS, encoding="utf-8"):
        r = json.loads(l)
        if r["label"] is not None: done.add((r["unit_id"], r["construct"]))
tasks = [(r["unit_id"], c, r["review_text"]) for r in rows for c in ([r["_c"]] if GOLDFILL else CONSTRUCTS) if (r["unit_id"], c) not in done]
print(f"[{MODEL}] {len(done)} done, {len(tasks)} to run", flush=True)
def work(t):
    uid, c, text = t
    if stop.is_set(): return uid, c, None, "skipped: stopped", {}
    return (uid, c) + CALL(PROMPTS[ASSIGN[uid]][c].replace("{text}", text))
lock = threading.Lock(); t0 = time.time()
with open(PROGRESS, "a", encoding="utf-8") as pf, ThreadPoolExecutor(WORKERS) as ex:
    for n, f in enumerate(as_completed([ex.submit(work, t) for t in tasks]), 1):
        uid, c, lab, err, meta = f.result()
        rec = {"unit_id": uid, "construct": c, "prompt": ASSIGN[uid], "label": lab, "model": MODEL, **meta}
        if err: rec["error"] = err
        with lock: pf.write(json.dumps(rec, ensure_ascii=False) + "\n"); pf.flush()
        if n % 1000 == 0: print(f"...{n}/{len(tasks)} ({time.time() - t0:.0f}s)", flush=True)
print("STOPPED EARLY (quota/auth). Re-run to resume." if stop.is_set() else f"[{MODEL}] finished", flush=True)
