"""What-if checks: apply v0.6 proposals (battery/v0.6-proposed.md) to existing v0.5 codes, after the fact.

These are labelled sensitivity checks in the report, never replacements for the v0.5 results.
- P1: no_channel_provided leaves the coder's values (it becomes metadata), so it is recoded to not_observable,
  and first_break no_channel (which only comes from it) becomes none.
- P3: first_break none with every step not_observable becomes unobserved.
"""
from agreement import STEPS, cohen_kappa


def p1_know_how(value):
    return "not_observable" if value == "no_channel_provided" else value


def p1_first_break(value):
    return "none" if value == "no_channel" else value


def p3_first_break(first_break, chain):
    if first_break == "none" and all(chain.get(s) == "not_observable" for s in STEPS):
        return "unobserved"
    return first_break


def stats(pairs):
    """(n, raw agreement, kappa) for a list of (a, b) code pairs."""
    if not pairs:
        return 0, None, None
    a, b = [p[0] for p in pairs], [p[1] for p in pairs]
    return len(pairs), sum(x == y for x, y in pairs) / len(pairs), cohen_kappa(a, b)


def expand(crosstab):
    """[[a, b, count], ...] -> list of (a, b) pairs, for cross-tabs transcribed from Ricky's tables."""
    return [(a, b) for a, b, n in crosstab for _ in range(n)]


def p1_check(pairs_know_how, pairs_first_break):
    """Agreement before and after P1 for know_how and first_break."""
    return {
        "chain know_how": (stats(pairs_know_how), stats([(p1_know_how(a), p1_know_how(b)) for a, b in pairs_know_how])),
        "first_break": (stats(pairs_first_break), stats([(p1_first_break(a), p1_first_break(b)) for a, b in pairs_first_break])),
    }
