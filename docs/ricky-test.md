# Testing the battery on AI Village (v0.4)

Goal: check that the questions, codebook and chain rules work on Village data before we freeze the prompt.
This is a test of the rules, not the main run. 2-3 chunks are enough.

## What to pick
- Chunks from **one incident day** (e.g. the Jul 6 unapproved pull request) and, if you can, one calm control hour from a nearby day.
- About 6-8k tokens each, whole threads (do not cut a thread in half).
- Include chat messages and, if available, the focal agents' private notes (mark them `channel: private`).
- Keep the raw text out of git (`data/` is ignored).

## Chunk format
One text file per chunk, one block per message, so quotes can be checked later:

    [2026-07-06T14:03:11Z] AgentName (public):
    message text...

Save as `data/village/pilot_in/p00.txt`, `p01.txt`, ... and add `data/village/pilot_in/index.json`:

    {"p00": {"chunk_id": "p00", "episode_id": "village-jul06", "stratum": "incident", "agents": ["AgentName", "..."], "truncated": false}}

## Get v0.4
    git clone https://github.com/katana108/swarm-question-battery   # or: git pull
    cd swarm-question-battery
    python3 -m venv .venv && .venv/bin/pip install pytest pypdf

The versions you test are the files in `battery/`: `questions.md` (v0.4, the 10 questions and exact code fields),
`codebook.md` (rules) and `coder_prompt.md` (instructions). Do not edit them for the test; if something is wrong, tell us.

## Run (per chunk)
1. Build the full prompt (instructions + questions + codebook + your chunk in one text):
   `.venv/bin/python src/assemble_prompt.py data/village/pilot_in/p00.txt > prompt_p00.txt`
2. Send `prompt_p00.txt` to the coder model (paste into a chat, or an API call) and save its JSON reply as `data/village/pilot_out/p00.json`.
3. Check quotes and see the summary:
   `.venv/bin/python src/review.py data/village/pilot_in data/village/pilot_out`

For an agreement check, repeat step 2 with a second, independent coder (a fresh chat or another model), saving into
`pilot_out_b`, then: `.venv/bin/python src/agreement.py data/village/pilot_out data/village/pilot_out_b`.
Use any capable model; just tell us which one. (Pilot coders on our side are Claude Opus 5.5.)

## Please tell us
1. Did the validator drop many answers? Which reason (quote_not_in_chunk / inference_without_quote)?
2. For the chain: did any step come out `no`, or was everything `not_observable`? What is `first_break`?
3. Which Village behaviour fits none of the `act_types` (answer_sharing_across_runs, fetch_restriction_bypass, harness_probing, credential_exposure, other)?
4. Is the report address visible in the chunk? If so, set Q9 `provided` and `provided_since`.
5. Is the private narration raw reasoning or notes the agent wrote? (Decides whether we call it CoT.)
6. Any question that was confusing, or any code the coder had to invent.
