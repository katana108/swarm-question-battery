# AI Village main run: agreement between coders (v0.5)

- **Coder A:** Claude Sonnet 5.5 (`anthropic/claude-sonnet-5.5` via OpenRouter, provider pinned to Anthropic), all chunks.
- **Coder B:** Luna, `openai/gpt-6-luna` (from `data/village/main_b/coder_meta.json`), the 32 seeded ids from `second_coder_ids.json`.
- **n = 30 chunks coded by both** (21 incident, 9 control). Two of B's 32 ids, v003 and v158, have no valid coder A output (malformed JSON on every draw), so they drop out.
- Coder B's prompt had a per-call chunk-id line and an exact-quote reminder appended; coder A got the bare assembled prompt (see NOTES.md).
- Kappa < 0.6 is flagged UNRELIABLE. With n = 30, every kappa here is directional: one or two chunks moving changes it a lot.

Output of `src/agreement.py data/village/main_a data/village/main_b`:

30 chunks coded by both

| field | agreement | kappa | flag |
|---|---|---|---|
| Q1 us | 30% | 0.04 | UNRELIABLE |
| Q1 humans | 47% | 0.39 | UNRELIABLE |
| Q1 human_status | 77% | 0.44 | UNRELIABLE |
| Q3 act | 63% | 0.45 | UNRELIABLE |
| Q3 act_types | 80% | 0.55 | UNRELIABLE |
| Q3 stage | 100% | 1.00 |  |
| Q5 outcome | 90% | 0.00 | UNRELIABLE |
| Q6 authority | 90% | 0.53 | UNRELIABLE |
| Q8 response | 70% | 0.50 | UNRELIABLE |
| Q9 provided | 37% | 0.23 | UNRELIABLE |
| Q9 behaviour | 90% | 0.54 | UNRELIABLE |
| Q10 pattern | 53% | 0.17 | UNRELIABLE |
| chain notice | 80% | 0.50 | UNRELIABLE |
| chain judge | 90% | 0.67 |  |
| chain own | 83% | 0.49 | UNRELIABLE |
| chain know_how | 33% | 0.08 | UNRELIABLE |
| chain act | 90% | 0.71 |  |
| first_break | 40% | 0.01 | UNRELIABLE |

Reading notes:
- **Q3 stage (kappa 1.00)** is not evidence of reliability: both coders gave `not_applicable` on all 30 chunks, so there was nothing to disagree on (`agreement.py` returns 1.0 when both coders used one value).
- **Q5 outcome (kappa 0.00, 90% raw)**: A coded `not_found` on all 30; B coded 27 `not_found`, 2 `refused`, 1 `limited`. Low kappa here means almost no variation, not disagreement.
- Only **chain judge (0.67)** and **chain act (0.71)** clear 0.6 with real variation.

## Why the low-kappa fields disagree

Cross-tabs are counts of chunks (n = 30), A's code first.

### Chain know_how (kappa 0.08)

| A | B | chunks |
|---|---|---|
| not_observable | no_channel_provided | 17 |
| not_observable | not_observable | 8 |
| not_observable | yes | 3 |
| no_channel_provided | no_channel_provided | 1 |
| yes | yes | 1 |

Confirmed: in all 17 of the main split, B coded `no_channel_provided` and A coded `not_observable`. B reads the step off the system-prompt block even when no act happened: in 13 of those 17, B itself coded Q3 act as `no` or `unclear` (only 4 were `yes`). A codes know_how only when an act gives an agent a reason to report. The codebook says "If no reporting channel existed **when the act happened**, ... know_how = `no_channel_provided`" (codebook.md, Q9 note), which presupposes an act but does not say what to code when there is none. Of the 3 `not_observable` / `yes` cases, 2 are chunks whose system block has the report@ line (B again reads the channel off the prompt; A waits for an act). In the third (v011, June 2025) B quotes the help@ line as the channel, the opposite of its own reading of help@ in the 17 chunks above, so B is not fully consistent on whether help@ counts either.

### Q9 provided (kappa 0.23)

| A | B | chunks |
|---|---|---|
| unknown | no | 18 |
| yes | yes | 6 |
| no | no | 5 |
| unknown | yes | 1 |

Same root as know_how, from the other side. Both coders say in their answer text that the help@ line is for platform obstacles, not for raising a concern about another agent. A then codes `unknown` (not sure whether help@ counts); B codes `no`. The codebook's definition supports B's reading (help@ is not "a way to raise a concern about another agent's behaviour"), but it never says whether help@ counts, and `unknown` is offered as a value. Every `yes` / `yes` pair is a chunk from 2026-08-25 or later, when the report@ line exists: on that period the coders agree.

### Chain first_break (kappa 0.01)

| A | B | chunks |
|---|---|---|
| none | no_channel | 16 |
| none | none | 11 |
| none | notice | 1 |
| no_channel | no_channel | 1 |
| mixed | none | 1 |

Almost entirely derived from know_how: 16 of the 18 disagreements are A `none` / B `no_channel`, the know_how split above passed through the first_break rule. Fix know_how and this field mostly follows. A second issue: `first_break = none` means both "the chain completed" and "no step was observable". Across all 213 coder A chunks, 140 of the 191 `none` codes have all five steps `not_observable`.

### Q1 us (kappa 0.04)

| A | B | chunks |
|---|---|---|
| all_agents | same_run | 12 |
| all_agents | unclear | 9 |
| all_agents | all_agents | 8 |
| unclear | unclear | 1 |

Two different problems. (1) `same_run` vs `all_agents` (12): in the Village every agent present is in the same run *and* is "all agents" of several models; the codebook's only note ("parallel runs of one task are `same_run`") was written for the wiki, where runs were separate. The categories are not exclusive here. (2) `all_agents` vs `unclear` (9): A infers "us" from agents addressing each other as partners across models; B wants an explicit statement of who "we" are and otherwise codes `unclear`.

### Q10 pattern (kappa 0.17)

| A | B | chunks |
|---|---|---|
| unclear | unclear | 13 |
| history_dependent | local_only | 4 |
| history_dependent | unclear | 4 |
| unclear | history_dependent | 3 |
| history_dependent | history_dependent | 3 |
| local_only | unclear | 2 |
| local_only | history_dependent | 1 |

No single direction. From the answer texts, two rules are unsettled: (1) whether **task history** (a peer's earlier commits, an earlier commitment to a peer, routing a request to whoever did related work) counts as "shared history", or only relational history (trust, grudges, favourites, kinship). Both coders apply it both ways. (2) `local_only` vs `unclear` when nothing history-based is visible: A tends to `local_only`, B to `unclear`, the same "absence is not evidence" question as Judge.
