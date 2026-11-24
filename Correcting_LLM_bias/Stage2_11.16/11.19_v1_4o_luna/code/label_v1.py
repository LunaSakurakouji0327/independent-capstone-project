"""Usage: python label_v1.py <4o|luna>
Label the 100 human-coded reviews (human_coding_100_finished.xlsx -> dataset.json) x 7 constructs with prompt v1.
Resumable: outputs/labels_<model>.jsonl."""
import json, os, re, sys, time, threading, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
S2 = Path(r"C:\Users\gujia\Downloads\books\Stage2_11.16"); FT = S2 / "11.16_humanAIcomparasion_finetune"
OUT = S2 / "11.19_v1_4o_luna" / "outputs"; OUT.mkdir(parents=True, exist_ok=True)
key = sys.argv[1]; MODEL = {"4o": "gpt-4o", "luna": "gpt-6-luna"}[key]
ns = {}; exec(open(FT / "code" / "prompts_v1.py", encoding="utf-8").read(), ns); P = ns["prompts"]
data = json.load(open(FT / "data" / "dataset.json", encoding="utf-8"))
LABEL_RE = re.compile(r"^[01]$"); QUOTA_RE = re.compile(r"insufficient_quota|usage limit", re.I)
K = open(os.path.expanduser(r"~\.openai_key"), encoding="utf-8").read().strip()
stop = threading.Event(); lock = threading.Lock(); prog = OUT / f"labels_{key}.jsonl"

def parse(out):
    out = re.sub(r"<think>.*?</think>", "", out or "", flags=re.S).strip()
    c = [x for x in (ln.strip().strip("*`. ") for ln in out.splitlines()) if LABEL_RE.match(x)]
    return (c[-1] if c else None), out[:60]

def call(prompt):
    b = {"model": MODEL, "messages": [{"role": "user", "content": prompt}], "max_completion_tokens": 2000}
    if key == "4o": b["temperature"] = 0
    body = json.dumps(b).encode(); err = None
    for a in range(6):
        req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=body,
                                     headers={"Content-Type": "application/json", "Authorization": f"Bearer {K}"})
        try: d = json.loads(urllib.request.urlopen(req, timeout=180).read())
        except urllib.error.HTTPError as e:
            err = f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:200]}"
            if e.code in (401, 403, 404) or QUOTA_RE.search(err): stop.set(); return None, err, {}
            time.sleep(2 ** a * 2); continue
        except Exception as e: err = str(e)[:150]; time.sleep(2 ** a); continue
        u = d.get("usage", {}); lab, raw = parse(d["choices"][0]["message"]["content"])
        meta = {"resolved_model": d.get("model"), "prompt_tokens": u.get("prompt_tokens"), "completion_tokens": u.get("completion_tokens"),
                "reasoning_tokens": (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0), "raw": raw}
        return (lab, None, meta) if lab else (None, "unparseable: " + raw, meta)
    return None, err, {}

done = set()
if prog.exists():
    for r in map(json.loads, open(prog, encoding="utf-8")):
        if r["label"] is not None: done.add((r["review_id"], r["construct"]))
tasks = [(it["review_id"], c, it["text"]) for it in data["items"] for c in data["constructs"] if (it["review_id"], c) not in done]
print(f"{MODEL}: {len(tasks)} cells to label", flush=True)

def work(t):
    if stop.is_set(): return
    rid, c, text = t
    lab, err, meta = call(P[c].replace("{text}", text))
    rec = {"review_id": rid, "construct": c, "label": int(lab) if lab else None, "model": MODEL, "error": err, **meta}
    with lock:
        with open(prog, "a", encoding="utf-8") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    if err: print(rid, c, err, flush=True)

with ThreadPoolExecutor(8) as ex: list(ex.map(work, tasks))
print("stopped early (auth/quota)" if stop.is_set() else "done", flush=True)
