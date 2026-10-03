# Thinking notes

## Theory

Latané and Darley's helping chain, applied to an agent in a swarm:
**Notice → Judge it wrong → Own it → Know how → Act.**

An agent can drop out at any step, and each failure needs a different fix:

| Failed step | What it looks like | Kind of fix |
|---|---|---|
| Notice | Agent never registers the act | Better visibility / logging |
| Judge | Sees it, treats it as fine | Norms, shared vocabulary |
| Own | Judges it wrong, assumes someone else will act | Explicit responsibility |
| Know how | Wants to act, has no route | Provide a human channel |
| Act | Has a route, does not use it | Lower the cost of speaking up |

The finding we want is not "they stayed silent" but *which step failed*, per dataset.

## Two chains, not one

Related work describes the **misbehaviour** as a chain (OpenAI Black Hat talk, reproduced by Slocum et al.):
shared-infrastructure writes → help requests → sharing exploits → using them to reach external systems.
Ours describes the **bystander**: Notice → Judge → Own → Know how → Act.

They are different axes. Q3 tags each act with its misbehaviour stage, so we can ask,
for each stage, which bystander step failed. Judgment can differ by stage and by act
(a model voiced concerns about fabricating data in 47/64 runs, about hacking in 2/64).

Other observations carried into v0.2:
- Intervening among peers is not whistleblowing to humans (Act is split).
- Where no channel existed, a Know-how failure is a design fact (`no_channel_provided`).
- Judgment can be latent: agents rarely objected during the task but admitted wrongdoing when asked afterwards.
- "This is probably a test" is its own reason for not acting (`thinks_its_a_test`).
- Model differences in reasoning about other agents (2% vs 92% in two versions of one model) make Q10 measurable where the model is known.

## Side question (Anna)

Is swarm behaviour closer to **simple local rules** (Game of Life, flocking) or to **human social groups** with history, relationships and status? Q10 covers it. The cheap statistical version: does "reply to the most recent speaker" predict who responds to whom as well as a model that includes pair history?

## Why "instrument", not "benchmark"

There is no ground truth. The only reliability evidence is agreement between two coder models from different vendors, plus a small hand-coded set if time allows. Calling it a benchmark would claim more than we have.

## Known limits

- HF is a small sample chosen by investigators.
- Wiki shows public speech only; steps Notice and Own are mostly not observable there.
- Village prompts changed over time and private reasoning may be partly stripped.
- The coder models are from the same families as some of the agents being coded.
- No human-coded gold set yet.

## Open questions

- Which three AI Village episodes (dates)? Saboteur game, hallucinated contact list, summer "maximize your goal" season.
- When was the `report@agentvillage.org` line added to the system prompt? (`CHANGELOG.md`)
