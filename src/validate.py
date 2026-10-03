"""Validate coder answers against the chunk text the coder saw.

Rules (battery/coder_prompt.md):
- every quote must be an exact substring of the chunk (paraphrases too)
- drop answers whose quotes are all speaker_type=investigator
- an inference with no quote is only allowed as not_found / not_observable
"""
import json


def check_answer(answer, chunk_text):
    """Return (ok, reason) for one answer dict that has `quotes`, `code`, `observability`."""
    quotes = answer.get("quotes") or []
    for q in quotes:
        if q.get("text", "") not in chunk_text:
            return False, "quote_not_in_chunk"
    if quotes and all(q.get("speaker_type") == "investigator" for q in quotes):
        return False, "only_investigator_quotes"
    if not quotes:
        empty_ok = (
            answer.get("observability") == "not_observable"
            or answer.get("value") == "not_observable"  # chain steps use `value`, not `code`
            or "not_found" in json.dumps(answer.get("code"))
        )
        if not empty_ok:
            return False, "inference_without_quote"
    return True, "ok"


def validate_result(result, chunk_text):
    """Check every question answer and chain step; return a list of (label, ok, reason)."""
    report = []
    for answer in result.get("answers", []):
        report.append((answer.get("q", "?"), *check_answer(answer, chunk_text)))
    for step, entry in (result.get("chain") or {}).items():
        if isinstance(entry, dict) and "quotes" in entry:
            report.append((f"chain:{step}", *check_answer(entry, chunk_text)))
    return report
