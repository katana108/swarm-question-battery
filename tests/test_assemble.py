from assemble_prompt import assemble, instructions


def test_prompt_contains_all_parts_in_order():
    out = assemble("[2026-01-01T00:00:00Z] A (public):\nhello")
    marks = ["You are coding a transcript", "=== QUESTIONS ===", "(v0.5)", "=== CODEBOOK ===", "=== TRANSCRIPT CHUNK ===", "hello"]
    positions = [out.index(m) for m in marks]
    assert positions == sorted(positions)


def test_instructions_exclude_markdown_fences():
    assert "```" not in instructions()


def test_check_frozen_passes_now_and_fails_on_tamper(tmp_path):
    import pytest
    from assemble_prompt import check_frozen

    check_frozen()  # real config matches the real files
    bad = tmp_path / "config.yaml"
    bad.write_text("battery_sha256:\n  questions.md: deadbeef\n")
    with pytest.raises(RuntimeError):
        check_frozen(bad)
