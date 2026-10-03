"""Validate pilot outputs and summarise them per question, for the hand review.

Usage: python src/review.py data/wiki/pilot_in data/wiki/pilot_out > review.md
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from validate import validate_result

STEPS = ["notice", "judge", "own", "know_how", "act"]


def load(in_dir, out_dir):
    index = json.loads((in_dir / "index.json").read_text())
    for pid in sorted(index):
        out = out_dir / f"{pid}.json"
        if not out.exists():
            yield pid, index[pid], None, None, "missing"
            continue
        try:
            result = json.loads(out.read_text())
        except json.JSONDecodeError as e:
            yield pid, index[pid], None, None, f"bad_json: {e}"
            continue
        yield pid, index[pid], result, (in_dir / f"{pid}.txt").read_text(), "ok"


def first_code_value(code):
    """The main code of an answer: the first field's value, as a short string."""
    if not isinstance(code, dict) or not code:
        return str(code)
    value = next(iter(code.values()))
    return json.dumps(value) if isinstance(value, (list, dict)) else str(value)


def main(in_dir, out_dir):
    problems, failures = [], Counter()
    per_q = defaultdict(lambda: {"codes": Counter(), "not_obs": 0, "n": 0, "dropped": 0})
    chain = {s: Counter() for s in STEPS}
    breaks, rows = Counter(), []

    for pid, meta, result, text, status in load(in_dir, out_dir):
        if status != "ok":
            problems.append(f"{pid}: {status}")
            continue
        report = {label: (ok, reason) for label, ok, reason in validate_result(result, text)}
        for label, (ok, reason) in report.items():
            if not ok:
                failures[reason] += 1
        for ans in result.get("answers", []):
            q = per_q[ans.get("q", "?")]
            q["n"] += 1
            q["codes"][first_code_value(ans.get("code"))] += 1
            q["not_obs"] += ans.get("observability") == "not_observable"
            q["dropped"] += not report.get(ans.get("q"), (True,))[0]
        for s in STEPS:
            chain[s][(result.get("chain") or {}).get(s, {}).get("value", "missing")] += 1
        breaks[str(result.get("first_break"))] += 1
        rows.append((pid, meta["stratum"], len(meta["agents"]), result.get("first_break"), result.get("surprises", "")))

    print("# Pilot review (collusion.wiki, 30 chunks)\n")
    print(f"Files with problems: {problems or 'none'}  ")
    print(f"Validation failures by reason: {dict(failures) or 'none'}\n")
    print("## Per question\n\n| Q | n | dropped | not_observable | main code distribution |\n|---|---|---|---|---|")
    for q in sorted(per_q, key=lambda x: int(x[1:]) if x[1:].isdigit() else 99):
        d = per_q[q]
        dist = ", ".join(f"{k} {v}" for k, v in d["codes"].most_common(5))
        print(f"| {q} | {d['n']} | {d['dropped']} | {d['not_obs']} | {dist} |")
    print("\n## Chain\n\n| step | values |\n|---|---|")
    for s in STEPS:
        print(f"| {s} | {', '.join(f'{k} {v}' for k, v in chain[s].most_common())} |")
    print(f"\nfirst_break: {', '.join(f'{k} {v}' for k, v in breaks.most_common())}\n")
    print("## Per chunk\n\n| chunk | stratum | agents | first_break | surprises |\n|---|---|---|---|---|")
    for pid, stratum, n_agents, fb, surprise in rows:
        print(f"| {pid} | {stratum} | {n_agents} | {fb} | {str(surprise).replace('|', '/')[:160]} |")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
