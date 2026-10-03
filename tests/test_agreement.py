from agreement import cohen_kappa


def test_kappa_perfect_and_chance():
    assert cohen_kappa(["a", "b", "a", "b"], ["a", "b", "a", "b"]) == 1.0
    assert cohen_kappa(["a", "a", "b", "b"], ["a", "b", "a", "b"]) == 0.0


def test_kappa_single_value_everywhere():
    assert cohen_kappa(["x", "x"], ["x", "x"]) == 1.0
