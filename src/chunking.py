"""Split one episode into chunks of whole revisions.

The chunk text is rendered once and stored: the quote validator checks quotes
against exactly this string, so it must never be rebuilt differently later.
"""

MAX_CHARS = 24000  # roughly 6-8k tokens
TRUNC_MARK = "\n[TRUNCATED]\n"


def render_row(row):
    return f"[{row['ts']}] {row['agent']}:\n{row['text']}\n"


def chunk_episode(rows, max_chars=MAX_CHARS, overlap=1):
    """Pack whole revisions into chunks of at most max_chars.

    A revision is never split. One bigger than max_chars is truncated and flagged.
    The last `overlap` revisions of a chunk repeat at the start of the next, if they fit.
    """
    blocks = []
    for row in rows:
        text = render_row(row)
        truncated = len(text) > max_chars
        if truncated:
            text = text[: max_chars - len(TRUNC_MARK)] + TRUNC_MARK
        blocks.append((row["rev_id"], text, truncated))

    groups, current, size = [], [], 0
    for block in blocks:
        if current and size + len(block[1]) > max_chars:
            groups.append(current)
            tail = current[-overlap:] if overlap else []
            tail_size = sum(len(b[1]) for b in tail)
            current = tail if tail_size + len(block[1]) <= max_chars else []
            size = sum(len(b[1]) for b in current)
        current.append(block)
        size += len(block[1])
    if current:
        groups.append(current)

    episode_id = rows[0]["episode_id"] if rows else ""
    return [
        {
            "chunk_id": f"{episode_id}#{i}",
            "episode_id": episode_id,
            "rev_ids": [b[0] for b in group],
            "agents": sorted({r["agent"] for r in rows if r["rev_id"] in {b[0] for b in group}}),
            "truncated": any(b[2] for b in group),
            "text": "".join(b[1] for b in group),
        }
        for i, group in enumerate(groups)
    ]
