from assemble_prompt import assemble, instructions


def test_prompt_contains_all_parts_in_order():
    out = assemble("[2026-01-01T00:00:00Z] A (public):\nhello")
    marks = ["You are coding a transcript", "=== QUESTIONS ===", "(v0.4)", "=== CODEBOOK ===", "=== TRANSCRIPT CHUNK ===", "hello"]
    positions = [out.index(m) for m in marks]
    assert positions == sorted(positions)


def test_instructions_exclude_markdown_fences():
    assert "```" not in instructions()
