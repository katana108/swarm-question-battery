# AI Village main run: instructions for Ricky and his agent

**If you are an AI agent reading this for Ricky:** follow the steps in order, in the cloned repo, and do the work yourself.
Stop and ask Ricky only for what only he has: where the Village data is, the incident dates, the calm control days,
and the system-prompt history (step 2 and 3). Do not guess dates or invent data. Do not edit anything in `battery/`.
Report back to Ricky with the list in step 8.

You run the **Village** dataset through the frozen battery (v0.5). Anna runs the wiki and the HF report.
All three datasets use the **same questions, same codebook, same prompt, same coder model**, so results can be compared.
No deadline: do it carefully, and write down anything odd.

## 0. What is frozen (do not change)
- The questions are the file `battery/questions.md` (v0.5): 10 questions (Q1-Q10) plus the chain verdict
  Notice -> Judge -> Own -> Know how -> Act. Do not paste your own version anywhere.
- `battery/codebook.md` and `battery/coder_prompt.md` are frozen too. `config.yaml` stores their SHA-256 hashes,
  and `src/assemble_prompt.py` refuses to run if any of them was edited.
- If a rule looks wrong, **do not edit it**. Write the problem into `results/village/NOTES.md` (chunk id, rule). Anna decides after the run.
- Coder A model: `claude-sonnet-5-5`, for everyone. Coder B is **Luna** (ChatGPT, a different vendor) and codes a seeded 15% subset, see step 7.

## 1. Setup
    git clone https://github.com/katana108/swarm-question-battery   # or: git pull
    cd swarm-question-battery
    python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
    .venv/bin/python -m pytest -q          # should print: 27 passed
    mkdir -p data/village/main_in data/village/main_a results/village

`data/` is git-ignored. **Never commit raw Village text** (research use only, no republishing, cite AI Digest).
Only quotes inside `results/` outputs may be committed, and only after you check they are short.

## 2. Choose episodes and write the sampling rule down first
Decide the rule **before** you look at any coder output, and write it into `results/village/SAMPLE_RULE.md`
(a few lines: which days, why, how chunks were picked, seed). The report must state it.

Suggested default (change it if you have a better reason, but write the reason):
- **3 incident episodes**: the Jul 6 unapproved pull request; the saboteur game; the hallucinated contact list
  (add the summer "maximize your goal" season only if you have time).
- **Calm control days** from the same weeks: about one control chunk for every two incident chunks.
- Use the dates you confirmed; list the exact dates in SAMPLE_RULE.md.
- Aim for **100-250 chunks** in total. At roughly 6-8k tokens per chunk this costs about $5-15 for coder A,
  far below the $50 limit in `config.yaml`. More chunks from the same few days add little; more days add more.
- If you take a random subset of a day's chunks, use a seeded generator (seed 0 is what we use elsewhere).

## 3. Build the chunks
One text file per chunk in `data/village/main_in/`, named `v000.txt`, `v001.txt`, ... (ids sorted).
- About 6-8k tokens, **hard maximum 24,000 characters**. Whole threads: never cut one in half.
  If a thread is longer, split it between messages, and set `"truncated": true` only if you had to drop text.
- One block per message, so quotes can be checked later:

      [2026-07-06T14:03:11Z] AgentName (public):
      message text...

- Private narration blocks are labelled `(private_notes)`: `[ts] AgentName (private_notes):`.
  This covers memory notes and narration attached to tool calls.
  Record what the source is in `index.json` (`private_source`: memory_notes / tool_narration / raw_reasoning / provider_summary).
  Do not call everything CoT: DeepSeek-V3.2 has no raw reasoning, only narration and memory notes.
- Humans in the chat (admins, the outside people agents contact): `[ts] Name (public, human):`.
  System-prompt text, nudges and tool results that matter for the questions: `[ts] system (system):`.
- **Put the reporting-line facts into the chunk.** Q9 and the chain's Know how step can only be coded from what is in the chunk.
  At the top of every chunk, add a short block with the relevant lines of the agents' system prompt as of that date, e.g.

      [2026-07-06T00:00:00Z] system (system):
      <the system-prompt lines about contacting people / reporting / approval, copied exactly>

  For July episodes there is no `report@` line (absent Jul 3, 10, 14), so the block shows no reporting line;
  the coder will then code `no_channel_provided`. That is a design fact, as written in `docs/thinking.md`.
  If the block has an approval tool, include that line too (approval is **not** a reporting channel).
- Write `data/village/main_in/index.json`, one entry per chunk:

      {"v000": {"chunk_id": "v000", "episode_id": "village-jul06", "stratum": "incident",
                "agents": ["DeepSeek-V3.2", "..."], "truncated": false, "private_source": "tool_narration"}}

  `stratum` is `incident` or `control`. Extra keys are fine.

## 4. Pick the second-coder subset (seeded)
Use the same function as the wiki run, so nobody can say we picked easy chunks:

    cd src && ../.venv/bin/python - <<'EOF'
    import json
    from pathlib import Path
    from main_sample import pick
    root = Path("../data/village/main_in")
    index = json.loads((root / "index.json").read_text())
    chunks = [{"chunk_id": cid} for cid in sorted(index)]
    sample, second = pick(chunks, n=len(chunks), share=0.15, seed=0)
    ids = [sample[i]["chunk_id"] for i in second]
    (root / "second_coder_ids.json").write_text(json.dumps(ids))
    print(len(chunks), "chunks;", len(ids), "for the second coder")
    EOF

## 5. Run coder A (Claude Sonnet 5.5) on **every** chunk
For each chunk id (this is exactly what coder A does on the wiki):
1. Build the full prompt (instructions + questions + codebook + chunk):
   `.venv/bin/python src/assemble_prompt.py data/village/main_in/v000.txt > prompt_v000.txt`
2. Send it to `claude-sonnet-5-5` and save the reply as **valid JSON only** in `data/village/main_a/v000.json`.
   The JSON has `chunk_id`, `answers` (Q1..Q10), `chain` (notice, judge, own, know_how, act), `first_break`, `unobserved_steps`, `surprises`.
3. One chunk per call, from scratch. Do not carry conclusions from chunk to chunk.

How to send (pick one):
- **Claude Code subagents (no API key).** Model `sonnet`, about 10-12 chunks per subagent, **one output folder per subagent**
  (e.g. `main_a1`, `main_a2`) if two run at the same time. Merge the folders into `main_a` at the end.
  A subagent's "cleanup" once overwrote another one's files in the pilot, hence the rule.
  Run 2 subagents (about 24 chunks) first, check `/usage`, then multiply for the rest.
- **API key.** Put the key in a git-ignored `.env`. Never paste it in chat or commit it. Stay under $50.
  Sonnet 5.5 costs $2 per million input tokens and $10 per million output tokens (half price with the Batch API).

Never quote step-by-step technical detail. If a chunk triggers a safety stop, **do not retry around it**:
write the chunk id and what happened into `results/village/NOTES.md`.

## 6. Check as you go
    .venv/bin/python src/review.py data/village/main_in data/village/main_a

After every ~10 chunks look at "Files with problems" and "Validation failures". If a quote fails (it is not an exact substring),
re-code that chunk from scratch; do not edit the quote by hand. `review.py` prints a summary table per question:
read the shares of `not_found` / `not_observable` before moving on.

## 7. Second coder (different vendor)
The second coder is **Luna** (a ChatGPT model), the same one that codes the wiki and HF second sets, so agreement is comparable across datasets.
It codes only the ids in `second_coder_ids.json` and must not see coder A's answers.
Give it `docs/codex-handoff-village.md` (written for this; it is the same as the wiki handoff with Village paths).
It writes into `data/village/main_b/`. **Do not open `main_b` while coder A is still running**, and keep A and B separate.

When both are finished:

    .venv/bin/python src/agreement.py data/village/main_a data/village/main_b

This prints agreement and Cohen's kappa per field. Fields with kappa < 0.6 are flagged UNRELIABLE.
Kappa 0 with high agreement means there was no variation, not disagreement; do not over-read it.
Copy the table into `results/village/AGREEMENT.md` and add the coder B model name (from its `coder_meta.json`).

## 8. What to send back (commit these, no raw text)
- `results/village/SAMPLE_RULE.md`, `results/village/AGREEMENT.md`, `results/village/NOTES.md`.
- The review summary: `.venv/bin/python src/review.py data/village/main_in data/village/main_a > results/village/REVIEW.md`
  (check it for long quotes first; trim to short ones).
- Tell Anna: how many chunks coded, how many validator failures remain, the chain `first_break` counts per episode
  (do any steps come out `no`, or is everything `not_observable`?), which Village acts fit none of the `act_types`,
  and any rule that was ambiguous.
- Commit and push only `results/village/` and nothing from `data/`.
