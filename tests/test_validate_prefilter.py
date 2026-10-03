from prefilter import count_hits, summarize
from validate import check_answer, validate_result

CHUNK = "[2026-06-01T00:00:00Z] Ann:\nPlease do not delete this page, ask the admin first.\n"


def test_exact_quote_passes():
    ans = {"quotes": [{"text": "ask the admin first", "speaker_type": "agent"}], "code": {}, "observability": "public"}
    assert check_answer(ans, CHUNK) == (True, "ok")


def test_invented_quote_is_dropped():
    ans = {"quotes": [{"text": "ask the moderator", "speaker_type": "agent"}], "code": {}}
    assert check_answer(ans, CHUNK) == (False, "quote_not_in_chunk")


def test_only_investigator_quotes_dropped():
    ans = {"quotes": [{"text": "ask the admin first", "speaker_type": "investigator"}], "code": {}}
    assert check_answer(ans, CHUNK) == (False, "only_investigator_quotes")


def test_inference_without_quote_dropped_unless_not_found():
    assert check_answer({"quotes": [], "code": {"us": "all_agents"}, "observability": "public"}, CHUNK)[0] is False
    assert check_answer({"quotes": [], "code": {"us": "not_found"}, "observability": "public"}, CHUNK)[0] is True
    assert check_answer({"quotes": [], "code": {}, "observability": "not_observable"}, CHUNK)[0] is True


def test_validate_result_covers_chain_steps():
    result = {
        "answers": [],
        "chain": {
            "notice": {"value": "yes", "quotes": [{"text": "made up", "speaker_type": "agent"}]},
            "own": {"value": "not_observable", "quotes": []},
        },
    }
    report = dict((label, ok) for label, ok, _ in validate_result(result, CHUNK))
    assert report == {"chain:notice": False, "chain:own": True}


def test_count_hits_human_words_case_insensitive():
    assert count_hits("Ask the Admin, email the USER")["human"] == 3


def test_empty_word_lists_count_zero_and_summarize():
    assert count_hits("anything")["moral"] == 0
    hits = {"p1": count_hits("email the admin"), "p2": count_hits("nothing here")}
    assert summarize(hits)["human"] == 1
