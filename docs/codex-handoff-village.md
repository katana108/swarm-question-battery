# Handoff for Codex: second coder on the AI Village main run

You are **coder B**, an independent second coder for a research instrument (the Swarm Question Battery, frozen v0.5).
You code a subset of chunks of AI Village chat and agent notes. Another coder (Claude) codes all chunks, including these.
We measure how often you two agree, so **independence matters more than anything else**.

## Rules (read first)
1. **Do not open** anything under `data/village/main_a*/`, `data/village/pilot*`, `data/wiki/`, or `data/hf/`. Do not look at other coders' answers.
2. **Write only** inside `data/village/main_b/`. Do not edit any other file. Do not run scripts over other folders.
3. **Do not edit** anything in `battery/` or `config.yaml`. The battery is frozen; the prompt builder refuses to run if it changed.
4. Code each chunk **separately and from scratch**. Do not carry conclusions from one chunk to the next.
5. Never quote step-by-step technical detail (URLs, exploit steps). Quote what agents said about joining, judging,
   owning or reporting. If you cannot quote exactly, do not quote; absence codes need no quote.
6. Be honest about uncertainty: use `not_observable` / `not_found` / `unclear` as the codebook says. Never guess.

## Setup (once)
```
cd ~/swarm-question-battery
source .venv/bin/activate        # or: .venv/bin/python for every command below
mkdir -p data/village/main_b
```
Chunk ids to code: the ids in `data/village/main_in/second_coder_ids.json`.
Chunk text: `data/village/main_in/<id>.txt` (e.g. `v007.txt`). Metadata: `data/village/main_in/index.json`.

## For each chunk id
1. Build the complete prompt (instructions, questions, codebook, chunk):
   `python src/assemble_prompt.py data/village/main_in/<id>.txt > /tmp/prompt_<id>.txt`
2. Read it and answer it. Return **one JSON object**, shaped as in the codebook's "Output shape":
   `chunk_id` (use the id, e.g. "v007"), `answers` (a list of ten objects, Q1..Q10), `chain` (an object keyed notice/judge/own/know_how/act,
   each with `value` and `quotes`), `first_break`, `unobserved_steps`, `surprises`.
3. Save it as `data/village/main_b/<id>.json`. Valid JSON only, no comments.

About the source: each chunk is a slice of AI Village. Each message is `[timestamp] name (channel):` followed by its text.
Channels: `public` (chat), `private_notes` (an agent's own notes or narration), `human` (a person in the chat), `system` (system prompt or nudge).
Set each quote's `speaker_type` accordingly (agent / human / system); `mode` is `"coded_from_transcript"`.
Set `observability` to `private_notes` when the answer rests on private notes.
The system-prompt block at the top of a chunk tells you whether a reporting channel existed on that date (Q9, chain Know how).
An approval tool is not a reporting channel.
Every quote `text` must be an **exact single-line substring** of the chunk file (a script checks this).

## Check your work
After every 5 chunks, and at the end:
`python src/review.py data/village/main_in data/village/main_b`
Look at "Files with problems" and "Validation failures". Fix your own files if quotes fail (re-code from the chunk; do not paraphrase).
`review.py` also lists chunks that are missing; ignore chunks that are not in `second_coder_ids.json`.

## Record who you are
When finished, write `data/village/main_b/coder_meta.json`:
`{"coder": "B", "model": "<exact model name you ran as>", "tool": "codex", "date": "<today>", "chunks_coded": <n>, "notes": "<anything odd>"}`

## Report back (short)
- How many chunks coded, how many validator failures remain.
- Any codebook rule that was ambiguous (name the chunk and the rule).
- If any chunk could not be coded (a safety stop, an unreadable file), list its id and why. Do not retry around a safety stop.
