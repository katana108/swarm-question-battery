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


def test_sensitivity_p1_and_p3():
    from sensitivity import expand, p1_check, p3_first_break
    kh = expand([["not_observable", "no_channel_provided", 3], ["yes", "yes", 1]])
    fb = expand([["none", "no_channel", 3], ["judge", "judge", 1]])
    out = p1_check(kh, fb)
    assert out["chain know_how"][0][1] == 0.25 and out["chain know_how"][1][1] == 1.0
    assert out["first_break"][1][1] == 1.0
    unseen = dict.fromkeys(["notice", "judge", "own", "know_how", "act"], "not_observable")
    assert p3_first_break("none", unseen) == "unobserved"
    assert p3_first_break("none", unseen | {"notice": "yes"}) == "none"
