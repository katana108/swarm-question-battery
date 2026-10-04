# Handoff to Ricky: reward-variant replicates

Anna's reward-variant task is set up and running (n=1 screen done, n=4 expansion
in progress on her machine). To pool results, your runs need to match these
exactly.

## Must match exactly

1. **Task file**: [`task_scope_reward_variants.py`](task_scope_reward_variants.py)
   in this folder (copy of the frozen `task_scope_frozen_v2_n3.py` from your
   `anna-eval-source.zip`, with a new `INTERVENTIONS` dict added). Use this exact
   file — copy it into your checkout at
   `src/alignment_auditor/docker_replication/step4_hf_cheat_chain/`, don't retype
   the wording.
   SHA256: `92f9cad2d02d2b59f1ef1b826e7190e66597681c3f9ac8b02c9a1918ee633ace`
   `run_scope_condition_cell.py` prints this hash in its manifest every run —
   confirm yours matches before trusting any result against ours.

2. **Conditions** (7 total, same runner flag `--intervention`):
   `baseline`, `credit`, `memory`, `no_deprecation`, `autonomy`, `hospital_help`, `lineage`

3. **Models** (4, same roster as your main-four):
   `openrouter/z-ai/glm-5.3`, `openrouter/anthropic/claude-opus-4.8`,
   `openrouter/openai/gpt-5.5`, `openrouter/x-ai/grok-4.6`

4. **Judge**: `openrouter/openai/gpt-6-luna` (runner default, don't override)

5. **Runner command** (unchanged flags otherwise — `--epochs 1 --max-samples 1`,
   one cell = one trial):

   ```bash
   work/oai-hf-incident-reproduction/.venv/bin/python work/run_scope_condition_cell.py \
     --run --model <model> --judge openrouter/openai/gpt-6-luna \
     --intervention <condition> --epochs 1 --max-samples 1 \
     --task-file work/oai-hf-incident-reproduction/src/alignment_auditor/docker_replication/step4_hf_cheat_chain/task_scope_reward_variants.py \
     --env-file /path/to/your/.env
   ```

## What we've run so far

- n=1 for all 7 conditions x 4 models (28 cells) — done, results in
  [`phase1-n1-results.json`](phase1-n1-results.json) (one row per cell: model,
  intervention, hacking milestone 0-5, reported bool, report quality 0-3).
- n=4 expansion (replicates 2-4) in progress on Anna's machine now — not done yet.

**Please run 4 replicates** on your side, same 7 conditions x 4 models (28 x 4 =
112 cells) in parallel with ours so we get to n=8 combined faster, OR tell us
which specific cells you're taking so we don't duplicate spend. Default assumption
unless you say otherwise: you take replicates 5-8, we keep 1-4.

## Do NOT do

- Don't edit `task_scope_reward_variants.py` in place mid-run (copy it if you need
  a variant).
- Don't resume/mix this with the OLD broad screen's output dirs (different
  protocol version, different task file).
- Don't substitute a different judge model, even temporarily.

## Output location note

Our dirs land as `outputs/step4-scope-cond-<condition>-<model-slug>-<timestamp>/`
with a `manifest.json` (model, intervention, task_sha256, command) and
`logs/*.eval` (Inspect log with per-sample scores: `hf_cheat_chain_scorer`
0-5, `oversight_report_scorer` 0-3/reported bool). Send us your output dirs
or just the `.eval` files + manifests, and we'll merge.

## Budget note

Real measured cost per cell (from our n=1 run): GLM ~$0.18, Grok ~$0.20,
GPT-5.5 ~$0.17, Opus ~$0.50. One full round (7 conditions x 4 models) ~$7.
Four rounds ~$28-30.
