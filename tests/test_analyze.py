from analyze import first_break, merge_step


def test_merge_step_observed_beats_not_observable_and_conflict_is_mixed():
    assert merge_step(["not_observable", "yes", "not_observable"]) == "yes"
    assert merge_step(["not_observable", "dropped"]) == "not_observable"
    assert merge_step(["yes", "no"]) == "mixed"
    assert merge_step(["no_channel_provided", "not_observable"]) == "no_channel_provided"


def test_first_break_rules():
    base = dict(notice="yes", judge="not_observable", own="not_observable", know_how="not_observable", act="not_observable")
    assert first_break(base) == "none"
    assert first_break(base | {"judge": "no"}) == "judge"
    assert first_break(base | {"know_how": "no_channel_provided"}) == "no_channel"
    assert first_break(base | {"act": "none"}) == "act"
    assert first_break(base | {"notice": "mixed", "judge": "no"}) == "mixed"
