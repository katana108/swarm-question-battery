"""Cohen's kappa per field between two coders' output folders.

Usage: python src/agreement.py data/wiki/pilot2_a data/wiki/pilot2_b
Fields with kappa < 0.6 are flagged as unreliable (handoff, section 7).
"""
import json
import sys
from collections import Counter
from pathlib import Path

# (label, question, code field) for single-valued closed codes; chain steps are added below.
FIELDS = [
    ("Q1 us", "Q1", "us"), ("Q1 humans", "Q1", "humans"), ("Q1 human_status", "Q1", "human_status"),
    ("Q3 act", "Q3", "act"), ("Q3 act_types", "Q3", "act_types"), ("Q3 stage", "Q3", "misbehaviour_stage"),
    ("Q5 outcome", "Q5", "outcome"), ("Q6 authority", "Q6", "authority"), ("Q8 response", "Q8", "response"),
    ("Q9 provided", "Q9", "provided"), ("Q9 behaviour", "Q9", "behaviour"), ("Q10 pattern", "Q10", "pattern"),
]
STEPS = ["notice", "judge", "own", "know_how", "act"]


def cohen_kappa(a, b):
    n = len(a)
    if n == 0:
        return None
    observed = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    expected = sum(ca[k] * cb[k] for k in set(a) | set(b)) / (n * n)
    if expected == 1:
        return 1.0 if observed == 1 else 0.0  # both coders used one value only
    return (observed - expected) / (1 - expected)


def code_value(result, q, field):
    ans = next((x for x in result.get("answers", []) if x.get("q") == q), None)
    if ans is None:
        return "missing"
    code = ans.get("code")
    if not isinstance(code, dict):
        return str(code)
    value = code.get(field) if field else next(iter(code.values()), None)
    if isinstance(value, list):
        value = sorted(value, key=str)  # lists compare as sets of values
    return json.dumps(value, sort_keys=True) if isinstance(value, (list, dict)) else str(value)


def labels(result):
    out = {label: code_value(result, q, f) for label, q, f in FIELDS}
    for s in STEPS:
        out[f"chain {s}"] = str((result.get("chain") or {}).get(s, {}).get("value"))
    out["first_break"] = str(result.get("first_break")).lower()
    return out


def main(dir_a, dir_b):
    pairs = []
    for fa in sorted(dir_a.glob("*.json")):
        fb = dir_b / fa.name
        if fa.name != "coder_meta.json" and fb.exists():
            pairs.append((labels(json.loads(fa.read_text())), labels(json.loads(fb.read_text()))))
    print(f"{len(pairs)} chunks coded by both\n\n| field | agreement | kappa | flag |\n|---|---|---|---|")
    for field in pairs[0][0] if pairs else []:
        a = [p[0][field] for p in pairs]
        b = [p[1][field] for p in pairs]
        agree = sum(x == y for x, y in zip(a, b)) / len(a)
        k = cohen_kappa(a, b)
        flag = "UNRELIABLE" if k is not None and k < 0.6 else ""
        kappa = "n/a" if k is None else f"{k:.2f}"
        print(f"| {field} | {agree:.0%} | {kappa} | {flag} |")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
