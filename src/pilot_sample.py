"""Pick ~30 chunks for the pilot, seeded and stratified.

Strata (see plan): multi-agent pages, pages with human-word hits, the
relay-coordination family, and single-agent controls.
"""
import json
import random
from pathlib import Path

from chunking import chunk_episode
from ingest import group_by_episode, ingest_revisions
from prefilter import count_hits

MIN_CHARS = 300  # skip chunks too short to say anything
STRATA = [("multi_agent", 15), ("human_hit", 8), ("relay_family", 4), ("control", 3)]


def classify(rows, family):
    agents = {r["agent"] for r in rows}
    human = sum(count_hits(r["text"])["human"] for r in rows) > 0
    tags = set()
    if len(agents) >= 2 and len(rows) >= 4:
        tags.add("multi_agent")
    if human:
        tags.add("human_hit")
    if family == "relay-coordination":
        tags.add("relay_family")
    if len(agents) == 1 and len(rows) <= 3 and not human:
        tags.add("control")
    return tags


def pick_chunks(episodes, families, seed=0, strata=STRATA):
    rng = random.Random(seed)
    tagged = {s: [] for s, _ in strata}
    for eid in sorted(episodes):
        for tag in classify(episodes[eid], families.get(eid)):
            if tag in tagged:
                tagged[tag].append(eid)
    chosen, used = [], set()
    for stratum, n in strata:
        pool = [e for e in tagged[stratum] if e not in used]
        rng.shuffle(pool)
        taken = 0
        for eid in pool:
            if taken == n:
                break
            chunks = [c for c in chunk_episode(episodes[eid]) if len(c["text"]) >= MIN_CHARS]
            if not chunks:
                continue
            chunk = dict(rng.choice(chunks), stratum=stratum)
            chosen.append(chunk)
            used.add(eid)
            taken += 1
    return chosen


if __name__ == "__main__":
    root = Path(__file__).parent.parent / "data" / "wiki"
    episodes = group_by_episode(ingest_revisions(root / "revisions.jsonl"))
    families = {}
    with open(root / "pages.jsonl") as fh:
        for line in fh:
            p = json.loads(line)
            families[p["page_id"]] = p["page_family"]
    chosen = pick_chunks(episodes, families)
    out = root / "pilot_chunks.jsonl"
    with open(out, "w") as fh:
        for c in chosen:
            fh.write(json.dumps(c) + "\n")
    print(f"wrote {len(chosen)} chunks to {out}")
    for stratum, _ in STRATA:
        print(stratum, sum(1 for c in chosen if c["stratum"] == stratum))
