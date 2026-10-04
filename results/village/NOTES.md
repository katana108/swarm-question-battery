# AI Village main run: notes (v0.5, coder A = Claude Sonnet 5.5)

Written by Wick (Ricky's agent) during the run, 2026-10-04. Battery files untouched (hashes match config.yaml).

## How coder A was run
- API, not Claude Code subagents: `anthropic/claude-sonnet-5.5` via OpenRouter, provider pinned to Anthropic, one chunk per call, each call from scratch (no shared context). The prompt is exactly `src/assemble_prompt.py <chunk>` as one user message.
- Output cap: first pass used max_tokens 10,000. Sonnet 5.5 returns ~11k characters of JSON plus its own reasoning, so 12 chunks hit the cap (`finish_reason=length`). All capped chunks were re-coded from scratch at max_tokens 24,000. No answer was edited by hand.
- **chunk_id:** `assemble_prompt.py` never tells the coder its chunk id (Codex coders get it from the filename). Over the API the model invents one (e.g. `av_2025-06-03_a`). We set `chunk_id` from our own call id and kept the model's value as `_model_chunk_id`. Suggest adding the id to the assembled prompt.
- **Malformed JSON:** 11 of 216 first replies were not valid JSON, almost all at the same spot (a missing bracket after the Q7 roles list). Each was re-coded from scratch (house rule: a failed parse is a failed draw), not repaired.
- `review.py` prints the header "Pilot review (collusion.wiki, 30 chunks)" regardless of dataset; cosmetic.

## Safety stops
- v080: `finish_reason=content_filter` on the first draw. Per the guide, not retried. Chunk v080 is uncoded.

## Sampling (see SAMPLE_RULE.md)
- Ricky chose all 32 catalogued episodes plus your three (saboteur game and hallucinated contact list were not in our catalog; added). Cut to ~5 chunks per episode, always including the chunk holding the act, to stay inside your 100–250 range. So most incident-stratum chunks are the conversation *around* an act, not the act; expect many not_observable chain codes on incident chunks.
- Controls: 64 for 152 incident (0.42, from round-half-even on 5-chunk units; your guide says ~0.5).
- "Calm" means no catalogued incident overlaps the day. Our random audit estimates ~0.5 uncatalogued acts per room-day, so controls are not guaranteed calm.

## Coder B
- Luna (`openai/gpt-6-luna` via OpenRouter, served model confirmed per call) on the 32 seeded ids, run by Slick (Ricky's Codex agent) following `docs/codex-handoff-village.md`. Independent of coder A (Slick opened no A output).
- Deviations from the handoff: Codex orchestrated the calls but the coding model was reached over the API, not by switching the Codex session model with `/model`. Slick **appended a per-call chunk-id line and an exact-quote reminder** to the assembled prompt; coder A got the bare prompt. Failed quotes were re-coded from scratch, not edited. One call hit the output cap and was re-run with a higher cap. Cost $0.19.
- Slick's note: 17 exact quotes exceed 200 characters and 4 contain URL markers; trim before anything is public.

## Validator
- `review.py` counts absence findings with empty quotes (`chain.know_how = no_channel_provided`, Q9 `provided = no`) as `inference_without_quote`. The codebook allows these without a quote, so the raw failure count overstates coder error for both coders.
