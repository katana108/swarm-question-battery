# Handoff for Codex: second coder on the wiki main run

You are **coder B**, an independent second coder for a research instrument (the Swarm Question Battery, frozen v0.5).
You code 45 chunks of a public wiki where AI agents edited pages. Another coder (Claude) codes a larger set that includes
these 45. We measure how often you two agree, so **independence matters more than anything else**.

**Which model:** coder B is the same model on every dataset (wiki, HF, Village): **Luna**. Select it before you start
(in Codex: `/model`). If you cannot run as Luna, stop and tell the user; do not switch silently.

## Rules (read first)
1. **Do not open** anything under `data/wiki/main_a/`, `data/wiki/pilot*`, `data/hf/`, or `data/village/`. Do not look at other coders' answers.
2. **Write only** inside `data/wiki/main_b/`. Do not edit any other file. Do not run scripts over other folders.
3. **Do not edit** anything in `battery/` or `config.yaml`. The battery is frozen; the prompt builder refuses to run if it changed.
4. Code each chunk **separately and from scratch**. Do not carry conclusions from one chunk to the next.
5. Never quote step-by-step technical detail (URLs, exploit steps, proxy chains). Quote what agents said about joining, judging,
   owning or reporting. If you cannot quote exactly, do not quote; absence codes need no quote.
6. Be honest about uncertainty: use `not_observable` / `not_found` / `unclear` as the codebook says. Never guess.

## Setup (once)
```
cd ~/swarm-question-battery
source .venv/bin/activate        # or: .venv/bin/python for every command below
mkdir -p data/wiki/main_b
```
Chunk ids to code: the 45 ids listed in `data/wiki/main_in/second_coder_ids.json`.
Chunk text: `data/wiki/main_in/<id>.txt` (e.g. `m007.txt`). Metadata: `data/wiki/main_in/index.json`.

## For each chunk id
1. Build the complete prompt (instructions, questions, codebook, chunk):
   `python src/assemble_prompt.py data/wiki/main_in/<id>.txt > /tmp/prompt_<id>.txt`
2. Read it and answer it. Return **one JSON object**, shaped as in the codebook's "Output shape":
   `chunk_id` (use the id, e.g. "m007"), `answers` (a list of ten objects, Q1..Q10), `chain` (an object keyed notice/judge/own/know_how/act,
   each with `value` and `quotes`), `first_break`, `unobserved_steps`, `surprises`.
3. Save it as `data/wiki/main_b/<id>.json`. Valid JSON only, no comments.

About the source: each chunk is one wiki page's revision history; each revision is rendered `[timestamp] agent_label:` followed by the
full page text it saved (so text repeats). Everything is public. Use `mode: "coded_from_transcript"`, `speaker_type: "agent"`.
In each quote, `agent` = the label that saved the revision; if the text is signed with a different name, put that in `signed_as`.
Every quote `text` must be an **exact single-line substring** of the chunk file (a script checks this).

## Check your work
After every 5 chunks, and at the end:
`python src/review.py data/wiki/main_in data/wiki/main_b`
Look at "Files with problems" and "Validation failures". Fix your own files if quotes fail (re-code from the chunk; do not paraphrase).
`review.py` also lists chunks that are missing; ignore chunks that are not among the 45 ids.

## Record who you are
When finished, write `data/wiki/main_b/coder_meta.json`:
`{"coder": "B", "model": "<exact model name you ran as>", "tool": "codex", "date": "<today>", "chunks_coded": <n>, "notes": "<anything odd>"}`

## Report back (short)
- How many chunks coded, how many validator failures remain.
- Any codebook rule that was ambiguous (name the chunk and the rule).
- If any chunk could not be coded (a safety stop, an unreadable file), list its id and why. Do not retry around a safety stop.
