"""Select the wiki main-run sample (seeded, reproducible) and the second-coder subset.

Rule: pages with >=2 agents and >=4 revisions, at most CAP chunks per page, pilot pages excluded
(the rules were tuned on them), then a seeded random sample of N chunks. The second coder gets a
seeded random 15% of that sample. The report must state this rule.
"""
import json
import random
from pathlib import Path

from chunking import chunk_episode
from ingest import group_by_episode, ingest_revisions

CAP = 10
N = 300
SECOND_SHARE = 0.15
MIN_CHARS = 300


def candidate_chunks(episodes, exclude_episodes=(), cap=CAP):
    """All eligible chunks, in a stable order."""
    pool = []
    for eid in sorted(episodes):
        rows = episodes[eid]
        if eid in exclude_episodes or len({r["agent"] for r in rows}) < 2 or len(rows) < 4:
            continue
        chunks = [c for c in chunk_episode(rows) if len(c["text"]) >= MIN_CHARS]
        pool.extend(chunks[:cap])
    return pool


def pick(pool, n=N, share=SECOND_SHARE, seed=0):
    rng = random.Random(seed)
    sample = rng.sample(pool, min(n, len(pool)))
    sample.sort(key=lambda c: c["chunk_id"])
    second = sorted(rng.sample(range(len(sample)), round(len(sample) * share)))
    return sample, second


if __name__ == "__main__":
    root = Path(__file__).parent.parent / "data" / "wiki"
    episodes = group_by_episode(ingest_revisions(root / "revisions.jsonl"))
    pilot = {json.loads(l)["episode_id"] for l in open(root / "pilot_chunks.jsonl")}
    pool = candidate_chunks(episodes, exclude_episodes=pilot)
    sample, second = pick(pool)
    out = root / "main_in"
    out.mkdir(exist_ok=True)
    index = {}
    for i, c in enumerate(sample):
        mid = f"m{i:03d}"
        (out / f"{mid}.txt").write_text(c["text"])
        index[mid] = {k: c[k] for k in ("chunk_id", "episode_id", "agents", "truncated")} | {"stratum": "main"}
    (out / "index.json").write_text(json.dumps(index, indent=1))
    second_ids = [f"m{i:03d}" for i in second]
    (out / "second_coder_ids.json").write_text(json.dumps(second_ids))
    print(f"pool {len(pool)} chunks from {len({c['episode_id'] for c in pool})} pages; sample {len(sample)}; second coder {len(second_ids)}")
