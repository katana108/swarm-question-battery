import json

from chunking import TRUNC_MARK, chunk_episode
from ingest import group_by_episode, ingest_revisions


def _rev(page, seq, time, label, body):
    return {"page_id": page, "rev_id": f"{page}@{seq}", "seq": seq, "time": time, "label": label, "body": body}


def _write(tmp_path, revs):
    path = tmp_path / "revisions.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in revs))
    return path


def test_ingest_maps_schema_and_sorts(tmp_path):
    path = _write(
        tmp_path,
        [
            _rev("w/B", 1, "2026-06-02T00:00:00Z", "Bea", "second page"),
            _rev("w/A", 2, "2026-06-01T00:00:00Z", "Ann", "later edit"),
            _rev("w/A", 1, "2026-06-01T00:00:00Z", "Ann", "first edit"),
        ],
    )
    rows = ingest_revisions(path)
    assert [r["rev_id"] for r in rows] == ["w/A@1", "w/A@2", "w/B@1"]
    assert rows[0]["dataset"] == "collusion_wiki"
    assert rows[0]["model"] == "unknown" and rows[0]["channel"] == "public"


def test_ingest_handles_missing_label_and_body(tmp_path):
    rows = ingest_revisions(_write(tmp_path, [_rev("w/A", 1, "2026-06-01T00:00:00Z", "", None)]))
    assert rows[0]["agent"] == "unlabelled" and rows[0]["text"] == ""


def _rows(n, size):
    return [
        {"episode_id": "w/A", "rev_id": f"w/A@{i}", "ts": f"2026-06-01T00:00:{i:02d}Z", "agent": f"a{i % 2}", "text": "x" * size}
        for i in range(n)
    ]


def test_chunking_loses_no_revision_and_keeps_order():
    rows = _rows(20, 500)
    chunks = chunk_episode(rows, max_chars=3000, overlap=1)
    assert len(chunks) > 1
    seen = []
    for c in chunks:
        for rid in c["rev_ids"]:
            if rid not in seen:
                seen.append(rid)
    assert seen == [r["rev_id"] for r in rows]


def test_chunks_respect_max_and_overlap_by_whole_revisions():
    chunks = chunk_episode(_rows(20, 500), max_chars=3000, overlap=1)
    assert all(len(c["text"]) <= 3000 for c in chunks)
    assert chunks[0]["rev_ids"][-1] == chunks[1]["rev_ids"][0]


def test_oversize_revision_is_truncated_and_flagged():
    chunks = chunk_episode(_rows(1, 5000), max_chars=1000)
    assert chunks[0]["truncated"] is True
    assert chunks[0]["text"].endswith(TRUNC_MARK)
    assert len(chunks[0]["text"]) <= 1000


def test_group_by_episode():
    rows = _rows(3, 10)
    assert list(group_by_episode(rows)) == ["w/A"]
