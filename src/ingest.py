"""Ingest collusion.wiki revisions into the shared schema.

Shared schema: dataset, episode_id, ts, agent, model, channel, text
(plus rev_id so every row can be traced back to the source file).
Episode = one wiki page and its revision history.
"""
import json
from pathlib import Path

DATASET = "collusion_wiki"


def ingest_revisions(path):
    """Read revisions.jsonl and return rows sorted by episode, then time, then revision number."""
    rows = []
    with open(path) as fh:
        for line in fh:
            r = json.loads(line)
            rows.append(
                {
                    "dataset": DATASET,
                    "episode_id": r["page_id"],
                    "ts": r["time"],
                    "agent": r["label"] or "unlabelled",
                    "model": "unknown",  # the dump has no model field
                    "channel": "public",
                    "text": r["body"] or "",
                    "rev_id": r["rev_id"],
                    "_seq": int(r["seq"]),
                }
            )
    rows.sort(key=lambda x: (x["episode_id"], x["ts"], x["_seq"]))
    for row in rows:
        del row["_seq"]
    return rows


def group_by_episode(rows):
    episodes = {}
    for row in rows:
        episodes.setdefault(row["episode_id"], []).append(row)
    return episodes


if __name__ == "__main__":
    data = Path(__file__).parent.parent / "data" / "wiki" / "revisions.jsonl"
    rows = ingest_revisions(data)
    print(f"{len(rows)} rows, {len(group_by_episode(rows))} episodes")
