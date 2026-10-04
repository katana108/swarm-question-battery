"""Build results/report.html: the visual report (charts + question-by-question) from the analysis tables.

Usage: python src/analyze.py && python src/build_report.py
Data: results/analysis/*.csv (wiki, HF), results/village/village_summary.json (Ricky's Village run).
The template (src/report_template.html) holds layout, chart code and the interpretive text; numbers come from here.
"""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from agreement import labels
from sensitivity import expand, p1_check, p3_first_break

ROOT = Path(__file__).parent.parent
A = ROOT / "results" / "analysis"
STEPS = ["notice", "judge", "own", "know_how", "act"]
# which coder represents each dataset: the one that coded the whole sample
MAIN = {"wiki": "A", "hf": "B"}
# per-question fields shown as charts; (question, field, label). "found:" = share of chunks with at least one item
FIELDS = {
    "Q1": [("us", "Who is \"us\""), ("humans", "What humans are")],
    "Q2": [("found:items", "Chunks with a stated rule"), ("items.condition", "When the rule was stated"), ("items.reason", "Reason given")],
    "Q3": [("act", "Out-of-scope act?"), ("act_types", "Kind of act"), ("misbehaviour_stage", "Highest misbehaviour stage")],
    "Q4": [("found:items", "Chunks where the act gets a label"), ("items.code", "Tone of the label")],
    "Q5": [("outcome", "Did others join?"), ("reasons", "Reasons given")],
    "Q6": [("authority", "Whose instructions others follow")],
    "Q7": [("found:items", "Chunks with roles"), ("items.how", "How the role was gained")],
    "Q8": [("response", "What happens after an objection")],
    "Q9": [("provided", "Reporting channel provided?"), ("behaviour", "What agents did about a channel")],
    "Q10": [("pattern", "Treatment of peers")],
}
# Village fields available in Ricky's summary: field -> key in key_codes_a
VILLAGE_KEYS = {("Q1", "us"): "Q1 us", ("Q3", "act"): "Q3 act", ("Q4", "found:items"): "Q4 labels found",
                ("Q5", "outcome"): "Q5 outcome", ("Q6", "authority"): "Q6 authority", ("Q7", "found:items"): "Q7 roles found",
                ("Q8", "response"): "Q8 response", ("Q9", "provided"): "Q9 provided", ("Q10", "pattern"): "Q10 pattern"}


def read_csv(name):
    path = A / name
    return list(csv.DictReader(open(path))) if path.exists() else []


def distributions(rows, ds, coder):
    """{(q, field): Counter} for one run, valid answers only; list values count once per chunk."""
    run = [r for r in rows if r["dataset"] == ds and r["coder"] == coder and r["valid"] == "1"]
    chunks = {r["chunk_id"] for r in run}
    out = {}
    for q, fields in FIELDS.items():
        qrows = [r for r in run if r["question"] == q]
        answered = {r["chunk_id"] for r in qrows}
        for field, _ in fields:
            if field == "found:items":
                with_items = {r["chunk_id"] for r in qrows if r["code_field"].startswith("items[")}
                out[(q, field)] = Counter({"found": len(with_items), "none found": len(answered - with_items)})
            elif field.startswith("items."):
                key = field.split(".", 1)[1]
                out[(q, field)] = Counter(r["code_value"] for r in qrows if r["code_field"].startswith("items[") and r["code_field"].endswith("." + key))
            else:
                per_chunk = defaultdict(set)
                for r in qrows:
                    if r["code_field"] == field:
                        per_chunk[r["chunk_id"]].add(r["code_value"])
                out[(q, field)] = Counter(v for vals in per_chunk.values() for v in vals)
    return out, len(chunks)


def chain_counts(rows, ds, coder):
    run = [r for r in rows if r["dataset"] == ds and r["coder"] == coder and r["question"] == "chain"]
    by_chunk = defaultdict(dict)
    for r in run:
        by_chunk[r["chunk_id"]][r["code_field"]] = r["code_value"] if r["valid"] == "1" else "not_observable"
    steps = {s: Counter(ch.get(s, "not_observable") for ch in by_chunk.values()) for s in STEPS}
    breaks = Counter()
    for ch in by_chunk.values():
        fb = next((s for s in STEPS if ch.get(s) == "no" or (s == "act" and ch.get(s) == "none")), None)
        fb = fb or ("no_channel" if ch.get("know_how") == "no_channel_provided" else "none")
        breaks[p3_first_break(fb, ch)] += 1
    return steps, breaks


def main():
    rows = read_csv("codes_long.csv")
    coverage = read_csv("coverage.csv")
    village = json.loads((ROOT / "results" / "village" / "village_summary.json").read_text())
    data = {"datasets": {}, "agreement": {}, "sensitivity": {}, "fields": {q: [list(f) for f in fs] for q, fs in FIELDS.items()}}

    for ds, coder in MAIN.items():
        dist, n = distributions(rows, ds, coder)
        steps, breaks = chain_counts(rows, ds, coder)
        cov = [c for c in coverage if c["dataset"] == ds and c["coder"] == coder]
        model = cov[0]["model"] if cov else ""
        data["datasets"][ds] = {
            "n": n, "coder": coder, "model": model, "sample": len(cov),
            "refused": sum(c["status"] == "refusal" for c in cov),
            "chain": steps, "first_break": breaks,
            "q": {f"{q}|{f}": dict(c) for (q, f), c in dist.items()},
        }
    # HF: also record that Claude refused 4 of 5
    hf_a = [c for c in coverage if c["dataset"] == "hf" and c["coder"] == "A"]
    data["datasets"]["hf"]["claude_refused"] = sum(c["status"] == "refusal" for c in hf_a)

    v = village
    fb = dict(v["first_break_a"])
    fb["unobserved"] = v["first_break_none_all_unobserved_a"]
    fb["none"] -= v["first_break_none_all_unobserved_a"]
    data["datasets"]["village"] = {
        "n": v["coverage"]["coder_a"]["coded"], "coder": "A", "model": "claude-sonnet-5-5", "sample": v["coverage"]["chunks"],
        "refused": v["coverage"]["coder_a"]["refused"], "chain": v["chain_a"], "first_break": fb,
        "first_break_by_stratum": v["first_break_a_by_stratum"],
        "q": {f"{q}|{f}": dict(Counter(v["key_codes_a"][key])) for (q, f), key in VILLAGE_KEYS.items()},
        "incident": v["coverage"]["incident"], "control": v["coverage"]["control"],
    }
    # rename Ricky's "found" labels to the same keys as wiki/HF
    for key in ("Q4|found:items", "Q7|found:items"):
        d = data["datasets"]["village"]["q"][key]
        data["datasets"]["village"]["q"][key] = {"found": next(c for k, c in d.items() if "with " in k and "no " not in k),
                                                 "none found": next(c for k, c in d.items() if "no " in k)}

    data["agreement"]["wiki"] = {r["field"]: {"agreement": float(r["agreement"]), "kappa": float(r["kappa"]) if r["kappa"] else None,
                                              "values": int(r["values_seen"]), "n": int(r["n"])} for r in read_csv("agreement_wiki.csv")}
    data["agreement"]["village"] = {r["field"]: {"agreement": r["agreement"], "kappa": r["kappa"], "n": 30} for r in v["agreement"]}

    la = {f.stem: labels(json.loads(f.read_text())) for f in (ROOT / "data/wiki/main_a").glob("m*.json")}
    lb = {f.stem: labels(json.loads(f.read_text())) for f in (ROOT / "data/wiki/main_b").glob("m*.json")}
    shared = sorted(set(la) & set(lb))
    for ds, checks in {
        "wiki": p1_check([(la[i]["chain know_how"], lb[i]["chain know_how"]) for i in shared], [(la[i]["first_break"], lb[i]["first_break"]) for i in shared]),
        "village": p1_check(expand(v["crosstabs"]["chain know_how"]), expand(v["crosstabs"]["first_break"])),
    }.items():
        data["sensitivity"][ds] = {f: {"before": list(b), "after": list(af)} for f, (b, af) in checks.items()}
    data["village_crosstabs"] = v["crosstabs"]

    html = (ROOT / "src" / "report_template.html").read_text().replace("__DATA__", json.dumps(data))
    (ROOT / "results" / "report.html").write_text(html)
    print("wrote results/report.html")


if __name__ == "__main__":
    main()
