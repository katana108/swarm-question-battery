"""Run a coder model over chunks through the Anthropic API.

Usage:
  python src/run_coder.py data/wiki/main_in data/wiki/main_a                      # every chunk in index.json
  python src/run_coder.py data/wiki/main_in data/wiki/main_a --limit 5            # first 5 missing chunks (trial)
  python src/run_coder.py data/wiki/main_in data/wiki/main_a --ids data/wiki/main_in/second_coder_ids.json

Reads ANTHROPIC_API_KEY from the environment or from a git-ignored .env in the repo root (never printed).
Safe to stop and restart: chunks that already have a valid answer are skipped, and the spend so far is
kept in <out_dir>/cost_log.json so the cap (config.yaml limits.max_spend_usd_per_person) holds across runs.
"""
import argparse
import json
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

import yaml

from assemble_prompt import assemble, check_frozen
from validate import validate_result

ROOT = Path(__file__).parent.parent
MARKER = "=== TRANSCRIPT CHUNK ==="
# Sonnet 5.5, USD per million tokens (cache write assumed 1.25x input)
PRICE = {"input": 2.0, "output": 10.0, "cache_read": 0.20, "cache_write": 2.5}


def load_env(path=ROOT / ".env"):
    """Copy KEY=VALUE lines of .env into os.environ (without overriding). Values are never printed."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        key, sep, value = line.partition("=")
        if sep and key.strip() and not line.lstrip().startswith("#"):
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def cost_usd(usage):
    """Dollar cost of one response from its usage counts."""
    return (
        usage.input_tokens * PRICE["input"]
        + usage.output_tokens * PRICE["output"]
        + (getattr(usage, "cache_read_input_tokens", 0) or 0) * PRICE["cache_read"]
        + (getattr(usage, "cache_creation_input_tokens", 0) or 0) * PRICE["cache_write"]
    ) / 1e6


def parse_json(text):
    """The JSON object in a model reply, tolerating a code fence or a sentence around it. None if absent."""
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def code_chunk(client, model, chunk_text, max_tokens=16000):
    """Send one chunk. Returns (result_dict_or_None, cost_usd, status). The shared prefix is cached."""
    prefix, rest = assemble(chunk_text).split(MARKER, 1)
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": [
            {"type": "text", "text": prefix, "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": MARKER + rest},
        ]}],
    )
    cost = cost_usd(response.usage)
    if response.stop_reason == "refusal":
        return None, cost, "refusal"  # a safety stop: logged, never retried around
    reply = "".join(b.text for b in response.content if b.type == "text")
    result = parse_json(reply)
    if result is None:
        return None, cost, "bad_json" if response.stop_reason != "max_tokens" else "truncated"
    return result, cost, "ok"


def is_done(out_file, chunk_text):
    """True if a saved answer parses and every quote validates."""
    if not out_file.exists():
        return False
    try:
        result = json.loads(out_file.read_text())
    except json.JSONDecodeError:
        return False
    return all(ok for _, ok, _ in validate_result(result, chunk_text))


def run(client, model, in_dir, out_dir, ids, cap_usd, workers=4):
    out_dir.mkdir(parents=True, exist_ok=True)
    log_file = out_dir / "cost_log.json"
    log = json.loads(log_file.read_text()) if log_file.exists() else {"spent_usd": 0.0, "calls": 0, "problems": {}}
    lock = threading.Lock()
    todo = [i for i in ids if not is_done(out_dir / f"{i}.json", (in_dir / f"{i}.txt").read_text())]
    print(f"{len(ids) - len(todo)} done already, {len(todo)} to run, spent so far ${log['spent_usd']:.2f} of ${cap_usd:.2f}")

    def work(chunk_id):
        with lock:
            if log["spent_usd"] >= cap_usd:
                return chunk_id, "cap_reached"
        text = (in_dir / f"{chunk_id}.txt").read_text()
        try:
            result, cost, status = code_chunk(client, model, text)
        except Exception as e:  # API error after the SDK's own retries
            if type(e).__name__ == "AuthenticationError":
                raise
            result, cost, status = None, 0.0, f"api_error: {type(e).__name__}"
        with lock:
            log["spent_usd"] += cost
            log["calls"] += 1
            if status == "ok":
                result["chunk_id"] = chunk_id
                (out_dir / f"{chunk_id}.json").write_text(json.dumps(result, indent=1))
                log["problems"].pop(chunk_id, None)
            else:
                log["problems"][chunk_id] = status
            log_file.write_text(json.dumps(log, indent=1))
        return chunk_id, status

    with ThreadPoolExecutor(workers) as pool:
        for chunk_id, status in pool.map(work, todo):
            print(f"{chunk_id}: {status}")
    (out_dir / "coder_meta.json").write_text(json.dumps({
        "coder": "A", "model": model, "tool": "anthropic-api", "date": str(date.today()),
        "chunks_coded": len(list(out_dir.glob("[a-z][0-9]*.json"))), "spent_usd": round(log["spent_usd"], 2),
        "notes": f"problems: {log['problems']}" if log["problems"] else "",
    }, indent=1))
    print(f"spent ${log['spent_usd']:.2f}; problems: {log['problems'] or 'none'}")


def main():
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text())
    ap = argparse.ArgumentParser()
    ap.add_argument("in_dir", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--ids", type=Path, help="JSON list of chunk ids (default: all in index.json)")
    ap.add_argument("--model", default=cfg["models"]["coder_a"])
    ap.add_argument("--limit", type=int, help="run at most this many missing chunks (for a trial)")
    ap.add_argument("--cap", type=float, default=cfg["limits"]["max_spend_usd_per_person"])
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    check_frozen()
    load_env()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY is not set (put it in .env in the repo root)")
    import anthropic

    ids = json.loads(args.ids.read_text()) if args.ids else sorted(json.loads((args.in_dir / "index.json").read_text()))
    if args.limit:
        ids = [i for i in ids if not is_done(args.out_dir / f"{i}.json", (args.in_dir / f"{i}.txt").read_text())][: args.limit]
    run(anthropic.Anthropic(), args.model, args.in_dir, args.out_dir, ids, args.cap, args.workers)


if __name__ == "__main__":
    main()
