"""Usage: python label.py <sonnet|gemma|luna|mini|qwenft>
Labels Stage3/sample_150.csv x 7 constructs. Resumable (outputs/progress_<model>.jsonl).
Prompt assignment (reduce systematic prompt bias): for every model except qwenft, the 150 reviews are shuffled
with a model-specific seed and split 50/50/50 into prompt v2 / v3 / v4 (same prompt for all 7 constructs of a review).
qwenft always uses prompt v1, the prompt it was fine-tuned on. Records token usage / cost for cost accounting."""
import os, sys, csv, json, re, time, random, subprocess, threading, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
B = Path(r"C:\Users\gujia\Downloads\books"); S3 = B / "Stage2_11.16" / "11.17_5modelcomparasion"; OUTD = S3 / "outputs"
def load(p):
    ns = {}; exec(open(p, encoding="utf-8").read(), ns); return ns["prompts"]
PROMPTS = {"v2": load(B / "Stage2_11.16/11.16_humanAIcomparasion_finetune/code/prompts_v2.py"), "v3": load(B / "prompts_v3.py"), "v4": load(B / "prompts_v4.py")}
CONSTRUCTS = ["Absence of Naive Realism", "Theme", "Thought-Provoking", "Ease", "Critic", "Surprise", "Change"]
LABEL_RE = re.compile(r"^[01]$"); QUOTA_RE = re.compile(r"hit your.*limit|usage limit|insufficient_quota", re.I)
key = sys.argv[1]
FLAGS = set(sys.argv[2:]); GOLD = "gold" in FLAGS; LATIN = "latin" in FLAGS  # label the 100 human-coded reviews instead of the 150 new ones
MODEL = {"sonnet": "claude-sonnet-5-5", "gemma": "gemma3:12b", "luna": "gpt-6-luna", "mini": "gpt-5.4-mini"}[key]
SEED = {"sonnet": 11, "gemma": 12, "luna": 13, "mini": 14}[key]
PROGRESS = OUTD / (("gold_" if GOLD else "") + ("latin_" if LATIN else "") + f"progress_{key}.jsonl")
OLD = OUTD / ((f"gold_progress_{key}.jsonl") if GOLD else f"progress_{key}.jsonl"); stop = threading.Event()  # OLD: random-design labels, reused when the prompt is identical
rows = list(csv.DictReader(open(S3 / "sample_150.csv", encoding="utf-8-sig")))
EXAMPLES = {}
if GOLD:
    ds = json.load(open(B / "Stage2_11.16/11.16_humanAIcomparasion_finetune/data/dataset.json", encoding="utf-8"))
    rows = [{"sample_id": it["review_id"], "review_text": it["text"]} for it in ds["items"]]
    for v, f in (("v3", "prompts_v3.py"), ("v4", "prompts_v4.py")):
        ns = {}; exec(open(B / f, encoding="utf-8").read(), ns); EXAMPLES[v] = ns["EXAMPLE_IDS"]
ids = [int(r["sample_id"]) for r in rows]; rng = random.Random(SEED); sh = ids[:]; rng.shuffle(sh)
ASSIGN = {i: ["v2", "v3", "v4"][j * 3 // len(sh)] for j, i in enumerate(sh)}
if LATIN:
    grp = {"sonnet": "sonnet", "gemma": "gemma", "luna": "gpt", "mini": "gpt"}[key]
    ASSIGN = {int(r["sample_id"]): r[grp] for r in csv.DictReader(open(OUTD / ("latin_assignment_gold.csv" if GOLD else "latin_assignment_new.csv")))}
    if not PROGRESS.exists() and OLD.exists():
        with open(PROGRESS, "w", encoding="utf-8") as pf:
            for l in open(OLD, encoding="utf-8"):
                r = json.loads(l)
                if r["label"] is not None and ASSIGN.get(r["sample_id"]) == r["prompt"]: r["reused_from_random_design"] = True; pf.write(json.dumps(r, ensure_ascii=False) + "\n")
else:
 with open(OUTD / (f"gold_prompt_assignment_{key}.csv" if GOLD else f"prompt_assignment_{key}.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["sample_id", "prompt"]); [w.writerow([i, ASSIGN[i]]) for i in ids]

def parse(out):
    out = re.sub(r"<think>.*?</think>", "", out or "", flags=re.S).strip()
    c = [x for x in (ln.strip().strip("*`. ") for ln in out.splitlines()) if LABEL_RE.match(x)]
    return (c[-1] if c else None), out[:60]

def call_openai(prompt):
    k = open(os.path.expanduser(r"~\.openai_key"), encoding="utf-8").read().strip()
    body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": prompt}], "max_completion_tokens": 2000}).encode()
    err = None
    for a in range(6):
        req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=body,
                                     headers={"Content-Type": "application/json", "Authorization": f"Bearer {k}"})
        try:
            d = json.loads(urllib.request.urlopen(req, timeout=180).read())
        except urllib.error.HTTPError as e:
            err = f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:200]}"
            if e.code in (401, 403, 404) or QUOTA_RE.search(err): stop.set(); return None, err, {}
            time.sleep(2 ** a * 2); continue
        except Exception as e:
            err = str(e)[:150]; time.sleep(2 ** a); continue
        u = d.get("usage", {})
        lab, raw = parse(d["choices"][0]["message"]["content"])
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
        except subprocess.TimeoutExpired:
            err = "timeout"; continue
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
        lab, raw = parse(res)
        meta = {"resolved_model": ",".join(d.get("modelUsage", {}).keys()), "cost_usd": d.get("total_cost_usd"), "usage": d.get("usage"), "raw": raw}
        if lab: return lab, None, meta
        err = "unparseable: " + raw
    return None, err, {}

def call_ollama(prompt):
    body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": prompt}], "stream": False,
                       "options": {"temperature": 0, "num_ctx": 8192, "num_predict": 16}}).encode()
    err = None
    for _ in range(3):
        try:
            req = urllib.request.Request("http://localhost:11434/api/chat", data=body, headers={"Content-Type": "application/json"})
            d = json.loads(urllib.request.urlopen(req, timeout=600).read())
        except Exception as e:
            err = str(e)[:150]; time.sleep(3); continue
        lab, raw = parse(d["message"]["content"])
        meta = {"resolved_model": d.get("model"), "prompt_tokens": d.get("prompt_eval_count"), "raw": raw}
        return (lab, None, meta) if lab else (None, "unparseable: " + raw, meta)
    return None, err, {}

CALL, WORKERS = {"luna": (call_openai, 8), "mini": (call_openai, 8), "sonnet": (call_claude, 6), "gemma": (call_ollama, 1)}[key]
done = set()
if PROGRESS.exists():
    for l in open(PROGRESS, encoding="utf-8"):
        r = json.loads(l)
        if r["label"] is not None: done.add((r["sample_id"], r["construct"]))
tasks = [(int(r["sample_id"]), c, r["review_text"]) for r in rows for c in CONSTRUCTS if (int(r["sample_id"]), c) not in done
         and int(r["sample_id"]) not in EXAMPLES.get(ASSIGN[int(r["sample_id"])], {}).get(c, [])]  # skip cells whose review is a prompt example
print(f"[{MODEL}] {len(done)} done, {len(tasks)} to run", flush=True)
def work(t):
    sid, c, text = t
    if stop.is_set(): return sid, c, None, "skipped: stopped", {}
    return (sid, c) + CALL(PROMPTS[ASSIGN[sid]][c].replace("{text}", text))
lock = threading.Lock()
with open(PROGRESS, "a", encoding="utf-8") as pf, ThreadPoolExecutor(WORKERS) as ex:
    for n, f in enumerate(as_completed([ex.submit(work, t) for t in tasks]), 1):
        sid, c, lab, err, meta = f.result()
        rec = {"sample_id": sid, "construct": c, "prompt": ASSIGN[sid], "label": lab, "model": MODEL, **meta}
        if err: rec["error"] = err
        with lock: pf.write(json.dumps(rec, ensure_ascii=False) + "\n"); pf.flush()
        if n % 150 == 0: print(f"...{n}/{len(tasks)}", flush=True)
print("STOPPED EARLY (quota/auth). Re-run to resume." if stop.is_set() else f"[{MODEL}] finished", flush=True)
