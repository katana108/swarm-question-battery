# Wiki pilot review (Oct 3, 2026)

Data: collusion.wiki revisions, 30 chunks (one page each), seeded stratified sample (`src/pilot_sample.py`).
Coders: Claude Opus 5.5 subagents on the Claude Code subscription. Prompt: battery v0.3 (commit bdd9b5c).
Raw outputs are git-ignored (they quote wiki text); this file holds codes and statistics only.

## Round 1 (battery v0.2, one coder per chunk)
- 0 invented quotes in 300 answers and 150 chain steps.
- Coders disagreed on first_break for the same kind of page (act vs own), because no rule said what to do when Judge is not observable.
- Q2, Q4, Q7 came back as free text; agent labels and in-text signatures often differ.
- Led to v0.3: closed codes, absence rule, attribution rule, first_break skips unobserved steps, bystander rule, act_type.

## Round 2 (battery v0.3, two independent coders on all 30 chunks)
Within-vendor agreement (both coders Opus). This tests whether the rules are clear, not cross-vendor reliability.

30 chunks coded by both

| field | agreement | kappa | flag |
|---|---|---|---|
| Q1 us | 73% | 0.55 | UNRELIABLE |
| Q1 humans | 97% | 0.00 | UNRELIABLE |
| Q1 human_status | 53% | 0.00 | UNRELIABLE |
| Q3 act | 80% | 0.62 |  |
| Q3 act_type | 97% | 0.94 |  |
| Q3 stage | 83% | 0.74 |  |
| Q5 outcome | 83% | 0.56 | UNRELIABLE |
| Q6 leader | 73% | 0.00 | UNRELIABLE |
| Q8 | 97% | 0.94 |  |
| Q9 provided | 100% | 1.00 |  |
| Q9 behaviour | 100% | 1.00 |  |
| Q10 | 80% | 0.60 |  |
| chain notice | 90% | 0.71 |  |
| chain judge | 100% | 1.00 |  |
| chain own | 100% | 1.00 |  |
| chain know_how | 100% | 1.00 |  |
| chain act | 100% | 1.00 |  |
| first_break | 100% | 1.00 |  |

Reading the table:
- Chain and first_break agree 100%, but only because the chain is empty on this source: every coder found no
  step coded `no` (everyone present takes part, no evaluative language, no human channel visible). The wiki
  cannot test the bystander chain; it shows group formation and norms (Q2, Q3, Q5-Q7) instead.
- Kappa 0.00 with high raw agreement (Q1 humans 97%) means almost no variation: both coders say "absent"
  nearly always. Not unreliability, just nothing to tell apart.
- Real disagreements: Q1 us and human_status, Q5 outcome, Q6 (missing field names, "unclear" vs "not_found"
  conventions), and Q3 act (borderline 0.62: where "yes" ends and "unclear" begins).

## Process notes
- One coder's clean-up script rewrote the other same-coder files in its folder (pilot2_b p15-p29): blanked
  `signed_as` where equal to the agent label and reformatted whitespace. Codes were checked intact afterwards.
  Coder A vs coder B independence was not affected. Future runs: one output folder per coder instance.
- One coder briefly saw summary lines of a same-coder half after finishing its own files.
