# Swarm Question Battery

An open-source **eval instrument (v0)** for multi-agent transcripts: a fixed set of 10 questions that a "coder model" answers over any swarm transcript. Each answer returns a category code plus verbatim quotes.

Built for the AI Swarm Dynamics hackathon (submission Sunday Oct 4, 17:00).

> Status: v0, work in progress. This is **not a benchmark**. There is no ground truth yet. Reliability evidence is agreement between two coder models from different vendors.

## The idea

Latané and Darley's helping chain, applied to an agent in a swarm:

**Notice → Judge it wrong → Own it → Know how → Act**

An agent can drop out at any step, and each failure needs a different fix. The question is not "did they stay silent?" but **which step failed** when agents did not speak up to humans.

A side question: is swarm behaviour closer to *simple local rules* (Game of Life, flocking) or to *human social groups* with history, relationships and status? (Q10)

## What is in this repo

| Path | What |
|---|---|
| [battery/questions.md](battery/questions.md) | The 10 questions, codes, and the chain verdict (the reusable part) |
| [battery/coder_prompt.md](battery/coder_prompt.md) | The coder prompt (draft, to be frozen after the pilot) |
| [battery/codebook.md](battery/codebook.md) | Codebook (to be written during the pilot) |
| [battery/extended.md](battery/extended.md) | Questions cut from the run, kept for later |
| [docs/handoff.md](docs/handoff.md) | Full project plan: data, pipeline, statistics, budget, timeline |
| [docs/thinking.md](docs/thinking.md) | Theory notes and open questions |
| `run.py` | Transcript in, long-format CSV out (not built yet) |
| `results/` | Coded tables (not produced yet) |

## Data

Raw data is **not** in this repo. See [data/README.md](data/README.md) and section 3 of the [handoff](docs/handoff.md) for sources and licence terms. We publish codes and short quotes only.

## Team

- Anna: questions and theory
- Ricky Mouser: statistics and analysis

## Licence

Code and questions: MIT (see [LICENSE](LICENSE)). The datasets keep their own licences.
