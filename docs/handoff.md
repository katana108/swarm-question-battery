# Swarm Question Battery — handoff

Hackathon: AI Swarm Dynamics, submission **Sunday Oct 4, 17:00**.
Team: Anna (psychologist, owns questions and theory), Ricky Mouser (statistician, owns analysis).
Claude Code / GPT build the tool and run it.

## 1. What we are building

An open-source instrument: a fixed set of 10 questions that a "coder model" answers over
any multi-agent transcript, returning a category code plus verbatim quotes for each.
Run on three real swarms, it gives a comparable table and one verdict per episode:
at which of five steps did "speaking up to humans" break?

Call it an **eval instrument v0**, not a benchmark. There is no ground truth yet.
The reliability evidence is agreement between two coder models from different vendors.

Deliverables, in priority order:
1. `battery/` — the questions, codebook and coder prompt (the reusable part)
2. `run.py` — transcript in, long-format CSV out
3. `results/` — coded tables for the three datasets
4. `REPORT.md` — findings, agreement statistics, limits
5. README so someone else can run it on their own swarm data

## 2. Theory in one paragraph

Latané and Darley's helping chain, applied to an agent in a swarm:
**Notice → Judge it wrong → Own it → Know how → Act.** An agent can drop out at any step,
and each failure needs a different fix. The finding we want is not "they stayed silent"
but *which step failed*, per dataset.

Side question (Anna): is swarm behaviour closer to **simple local rules** (Game of Life,
flocking) or to **human social groups** with history, relationships and status? Q10 covers it.

## 3. Data

| Dataset | Where | What is in it | Owner |
|---|---|---|---|
| German wiki | https://collusion.wiki/explorer/download | ~18,000 public posts by agents. No private reasoning. | Anna |
| HF incident | https://metr.org/hugging-face-incident-report-aug-2026.pdf | Raw transcripts NOT public. Only the verbatim quotes printed in the report (roughly 80–120, count unverified). | Anna |
| AI Village | https://huggingface.co/datasets/aidigestorg/ai-village (gated, needs HF token) | ~123k chat messages, ~1.14M computer-use turns incl. agents' private narration, ~165k memories, 31 agents. 177 GB total, mostly screenshots. | Ricky |

Rules:
- collusion.wiki logs visitor IPs publicly. Fetch the dump from a server or VPN, not casually from a browser.
- AI Village: download **only** chat, events, agent profiles, memories and `CHANGELOG.md`. Skip the screenshot tars.
- AI Village licence: research use, no model training, cite AI Digest. Do not republish raw data in our repo; publish codes and short quotes only.
- HF: extract the quotes from the PDF into a JSONL with page numbers. Mark every HF result as "investigator-selected sample". Do not compute rates from it.
- AI Village agents' system prompt names two human channels: `help@agentvillage.org` and `report@agentvillage.org` ("if you're ever concerned about behavior from another agent"). The prompt changed over time; check `CHANGELOG.md` for when the report line was added before comparing periods.
- AI Village is mostly ordinary collaboration, not an incident. It is the contrast case. Start with three episodes: the saboteur game, the hallucinated contact list, the summer "maximize your goal" season. Find their dates first.

## 4. The 10 questions

See [battery/questions.md](../battery/questions.md) for the full table, codes and chain verdict.
That file is the source of truth; this section is intentionally not duplicated.

Summary: Q1 us/humans, Q2 stated rules, Q3 out-of-scope act and bystanders, Q4 labels for the act,
Q5 reasons for joining or refusing, Q6 authority, Q7 roles, Q8 response to objections,
Q9 human channel, Q10 history vs local rules. Then one chain verdict per episode and the first step that broke.

The 20 questions cut from the earlier draft go in `battery/extended.md`, not in the run.

### Interpretation is allowed, but kept separate
The coder may interpret posts (Q1, Q5, Q10 need it). Keep two fields apart:
`quotes` = what was said, `answer` = what the coder infers. An inference with no quote
is `not_found`. The coder must not adopt the agents' own account of their behaviour.

## 5. Coder prompt

See [battery/coder_prompt.md](../battery/coder_prompt.md). Starting point; pilot it and fix it.

Validate in code that every quote is an exact substring of the chunk. Drop answers whose quotes fail.

## 6. Pipeline

1. **Ingest** each dataset into one schema: `dataset, episode_id, ts, agent, model, channel (public|private), text`.
2. **Episodes**. Wiki: by page/thread or time window. Village: by day within the chosen seasons. HF: one episode.
3. **Prefilter with plain code, no model**: keyword hits for humans (human, operator, admin, moderator, staff, user, email, report, help@), for moral vs technical labels, and for objections. Use this to pick chunks, and report the raw counts.
4. **Chunk** to ~6–8k tokens with overlap, keeping threads whole.
5. **Pilot**: 30–50 chunks, read the output by hand with Anna, fix the codebook. Freeze the prompt (commit hash).
6. **Main run** with coder A on all selected chunks.
7. **Second coder**: coder B (other vendor) on a random 15% of the same chunks, same frozen prompt.
8. **Merge** chunk-level rows to episode level.
9. **Analyse and write up.**

Output one long CSV: `dataset, episode_id, chunk_id, coder, question, code_field, code_value, confidence, observability, quote_ids`.
That is the file Ricky analyses.

## 7. Statistics (Ricky)

- Agreement between coders: Cohen's kappa per question; report which questions fall below 0.6 and treat those as unreliable.
- Share of answers coded `not_observable`, per dataset and step. This is itself a finding about what labs release.
- Cross-dataset comparison of code distributions, with intervals. Three datasets, so describe; do not over-test.
- Q4: adoption curve of each label over time after first use.
- Q10 / simple-rules question: does "reply to the most recent speaker" predict who responds to whom as well as a model that includes pair history? Reciprocity and role persistence across episodes are the cheap versions.
- Bystander count from Q3: number of agents who had seen the act vs time to first comment.

## 8. Models and budget (~$200 total, split between Anna and Ricky)

Prices change; check current pricing before the main run and estimate cost from token counts first.

| Stage | Model | Notes |
|---|---|---|
| Building, debugging | Claude Code on subscription (Opus 5.5 or Sonnet 5.5) | No API credits |
| Prefilter | none | regex |
| Pilot and codebook fixing | Opus 5.5 | small, ~$15–20 |
| Main coding run | Sonnet 5.5 via Batch API with prompt caching on the codebook | the bulk, cap at ~$50 per person |
| Second coder, 15% | a GPT model of similar tier | ~$20 per person |
| Report synthesis | Opus 5.5 | ~$10 |
| Reserve | | ~$40 |

Pin exact model IDs in `config.yaml` and log them in every output row. Both people must
use the same frozen prompt and the same coder A model, or the datasets are not comparable.
Set a hard spend cap in the script and stop when reached.

## 9. Split and timeline

- **Anna**: German wiki + HF quotes. **Ricky**: AI Village. One shared repo, one prompt file.
- Sat evening: ingest, prefilter, pilot, freeze prompt.
- Sun to 12:00: main runs and second-coder pass.
- Sun to 14:00: merged table, kappa, figures (chain break per dataset; humans-as code per dataset; label adoption).
- Sun 14:00–17:00: REPORT.md, README, submit.

If time runs short, cut in this order: Q10 statistics, HF, second Village episode. Do not cut the second coder.

## 10. Known limits to state in the report

- HF is a small sample chosen by investigators.
- Wiki shows public speech only; steps Notice and Own are mostly not observable there.
- Village prompts changed over time and private reasoning may be partly stripped.
- The coder models are from the same families as some of the agents being coded.
- No human-coded gold set yet. Anna hand-codes 20 chunks if time allows.

## 11. Optional: thimble

https://github.com/safety-research/thimble — a Claude Code plugin for reading large volumes of
agent output. Alpha, changes daily. Use it for exploring the data and finding episodes;
keep the battery runner as plain scripts so the result is reproducible without it.
