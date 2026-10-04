"""Run coder B (OpenAI, default gpt-6-luna) over the second-coder chunks. Same resume, cap and checks as run_coder.py.

Usage:
  python src/run_coder_openai.py data/wiki/main_in data/wiki/main_b --limit 3     # trial
  python src/run_coder_openai.py data/wiki/main_in data/wiki/main_b               # the 45 ids in main_in/second_coder_ids.json

Reads OPENAI_API_KEY from the environment or the git-ignored .env. Coder B never sees coder A's answers:
each call contains only the frozen prompt and one chunk.
"""
import argparse
import json
import os
from pathlib import Path

import yaml

from assemble_prompt import assemble, check_frozen
from run_coder import ROOT, is_done, load_env, parse_json, run

# gpt-6-luna, USD per million tokens (developers.openai.com/api/docs/models/gpt-6-luna)
PRICE = {"input": 0.10, "cached": 0.01, "output": 0.50}


def cost_usd(usage):
    """Dollar cost of one response; input_tokens includes the cached ones, output includes reasoning."""
    cached = getattr(getattr(usage, "input_tokens_details", None), "cached_tokens", 0) or 0
    return ((usage.input_tokens - cached) * PRICE["input"] + cached * PRICE["cached"] + usage.output_tokens * PRICE["output"]) / 1e6


def code_chunk(client, model, chunk_text, max_tokens=16000):
    """Send one chunk through the Responses API. Returns (result_or_None, cost_usd, status)."""
    response = client.responses.create(model=model, input=assemble(chunk_text), max_output_tokens=max_tokens)
    cost = cost_usd(response.usage)
    refused = any(c.type == "refusal" for item in response.output if item.type == "message" for c in item.content)
    if refused:
        return None, cost, "refusal"  # a safety stop: logged, never retried around
    result = parse_json(response.output_text)
    if result is None:
        return None, cost, "truncated" if response.status == "incomplete" else "bad_json"
    return result, cost, "ok"


def main():
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text())
    ap = argparse.ArgumentParser()
    ap.add_argument("in_dir", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--ids", type=Path, help="JSON list of chunk ids (default: in_dir/second_coder_ids.json)")
    ap.add_argument("--model", default=cfg["models"]["coder_b"])
    ap.add_argument("--limit", type=int, help="run at most this many missing chunks (for a trial)")
    ap.add_argument("--cap", type=float, default=cfg["limits"]["max_spend_usd_per_person"])
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    check_frozen()
    load_env()
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set (put it in .env in the repo root)")
    import openai

    ids = json.loads((args.ids or args.in_dir / "second_coder_ids.json").read_text())
    if args.limit:
        ids = [i for i in ids if not is_done(args.out_dir / f"{i}.json", (args.in_dir / f"{i}.txt").read_text())][: args.limit]
    run(openai.OpenAI(), args.model, args.in_dir, args.out_dir, ids, args.cap, args.workers,
        coder_fn=code_chunk, coder="B", tool="openai-api")


if __name__ == "__main__":
    main()
