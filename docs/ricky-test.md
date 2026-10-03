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

## Run
1. Give a model `battery/coder_prompt.md` (the block in it), `battery/questions.md`, `battery/codebook.md` and one chunk.
2. Save its JSON answer as `data/village/pilot_out/p00.json`.
3. Check quotes and get the summary: `python src/review.py data/village/pilot_in data/village/pilot_out`

Use two different coder instances if you can (folders `pilot_a`, `pilot_b`), then `python src/agreement.py data/village/pilot_a data/village/pilot_b`.

## Please tell us
1. Did the validator drop many answers? Which reason (quote_not_in_chunk / inference_without_quote)?
2. For the chain: did any step come out `no`, or was everything `not_observable`? What is `first_break`?
3. Which Village behaviour fits none of the `act_types` (answer_sharing_across_runs, fetch_restriction_bypass, harness_probing, credential_exposure, other)?
4. Is the report address visible in the chunk? If so, set Q9 `provided` and `provided_since`.
5. Is the private narration raw reasoning or notes the agent wrote? (Decides whether we call it CoT.)
6. Any question that was confusing, or any code the coder had to invent.
