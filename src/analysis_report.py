"""Render results/ANALYSIS.md from the tables built in analyze.py. Counts only; no quote text."""
from collections import Counter

from agreement import STEPS
from analyze import chain_values, first_break

# (question, code field) summarised per run; list fields count each value once per chunk
KEY_CODES = [
    ("Q1", "us"), ("Q1", "humans"), ("Q3", "act"), ("Q3", "act_types"), ("Q3", "misbehaviour_stage"),
    ("Q5", "outcome"), ("Q5", "reasons"), ("Q6", "authority"), ("Q8", "response"),
    ("Q9", "provided"), ("Q9", "channel_kind"), ("Q9", "behaviour"), ("Q10", "pattern"),
]


def fmt(counter):
    return ", ".join(f"{k} {v}" for k, v in counter.most_common()) or "-"


def run_name(chunks):
    c = chunks[0]
    return f"{c['dataset']} / coder {c['coder']} ({c['model']})"


def valid_answers(chunks, q):
    for c in chunks:
        if c["result"] is None or q in c["failed"]:
            continue
        ans = next((a for a in c["result"].get("answers", []) if a.get("q") == q), None)
        if ans:
            yield ans


def coverage(runs, ep_rows):
    lines = ["| run | chunks | coded | refused | other problems | episodes coded |", "|---|---|---|---|---|---|"]
    for chunks in runs:
        status = Counter(c["status"] for c in chunks)
        other = sum(v for k, v in status.items() if k not in ("coded", "refusal"))
        eps = sum(1 for e in ep_rows if (e["dataset"], e["coder"]) == (chunks[0]["dataset"], chunks[0]["coder"]))
        lines.append(f"| {run_name(chunks)} | {len(chunks)} | {status['coded']} | {status['refusal']} | {other} | {eps} |")
    return lines


def validation(runs):
    qs = [f"Q{i}" for i in range(1, 11)] + [f"chain:{s}" for s in STEPS]
    lines = ["| run | " + " | ".join(qs) + " |", "|---|" + "---|" * len(qs)]
    for chunks in runs:
        coded = [c for c in chunks if c["result"] is not None]
        lines.append(f"| {run_name(chunks)} | " + " | ".join(str(sum(q in c["failed"] for c in coded)) for q in qs) + " |")
    return lines


def chain_tables(runs, ep_rows):
    lines = []
    for chunks in runs:
        coded = [c for c in chunks if c["result"] is not None]
        eps = [e for e in ep_rows if (e["dataset"], e["coder"]) == (chunks[0]["dataset"], chunks[0]["coder"])]
        lines += [f"**{run_name(chunks)}**: {len(coded)} chunks, {len(eps)} episodes", "",
                  "| step | chunk level | episode level |", "|---|---|---|"]
        for s in STEPS:
            chunk_vals = Counter(str((c["result"].get("chain") or {}).get(s, {}).get("value")) for c in coded if f"chain:{s}" not in c["failed"])
            lines.append(f"| {s} | {fmt(chunk_vals)} | {fmt(Counter(e[s] for e in eps))} |")
        lines.append(f"| **first_break** | {fmt(Counter(first_break(chain_values(c)) for c in coded))} | {fmt(Counter(e['first_break'] for e in eps))} |")
        lines.append("")
    return lines


def key_codes(runs):
    lines = ["| question | field | " + " | ".join(run_name(r) for r in runs) + " |", "|---|---|" + "---|" * len(runs)]
    for q, field in KEY_CODES:
        cells = []
        for chunks in runs:
            counter = Counter()
            for ans in valid_answers(chunks, q):
                value = (ans.get("code") or {}).get(field)
                counter.update(set(map(str, value)) if isinstance(value, list) else [str(value)])
            cells.append(fmt(counter))
        lines.append(f"| {q} | {field} | " + " | ".join(cells) + " |")
    return lines


def agreement_tables(agree):
    lines = []
    for ds, (rows, n) in agree.items():
        lines += [f"**{ds}**: {n} chunks coded by both coders", "", "| field | n | agreement | kappa | values seen | flag |", "|---|---|---|---|---|---|"]
        for r in rows:
            agreement = "-" if r["agreement"] is None else f"{r['agreement']:.0%}"
            kappa = "n/a" if r["kappa"] is None else f"{r['kappa']:.2f}"
            lines.append(f"| {r['field']} | {r['n']} | {agreement} | {kappa} | {r['values_seen']} | {r['flag']} |")
        lines.append("")
    return lines


def village_section(v):
    """Village from Ricky's transcribed summary (results/village/village_summary.json)."""
    cov, a = v["coverage"], v["coverage"]["coder_a"]
    lines = [f"Source: Ricky's run, transcribed from `results/village/` ({', '.join(f.split('/')[-1] for f in v['source'])}). "
             "The raw Village data is not in this repo. **Unlike wiki/HF, these counts include answers that failed validation.**", "",
             f"- {cov['chunks']} chunks ({cov['incident']} incident from {cov['incident_units']} units, {cov['control']} control).",
             f"- Coder A, {a['model']}: {a['coded']} coded, {a['refused']} refused, {a['bad_json']} with invalid JSON on every draw.",
             f"- Coder B, {cov['coder_b']['model']}: {cov['coder_b']['coded']} coded; {cov['shared']} shared with A "
             f"({cov['shared_incident']} incident, {cov['shared_control']} control).", "",
             "| step | coder A, chunk level |", "|---|---|"]
    lines += [f"| {s} | {fmt(Counter(v['chain_a'][s]))} |" for s in STEPS]
    lines += [f"| **first_break** | {fmt(Counter(v['first_break_a']))} |", ""]
    lines += ["| first_break by stratum | values |", "|---|---|"]
    lines += [f"| {k} | {fmt(Counter(c))} |" for k, c in v["first_break_a_by_stratum"].items()]
    lines += ["", f"{v['first_break_none_all_unobserved_a']} of the {v['first_break_a']['none']} `none` have all five steps `not_observable`.", "",
              "| key code (coder A) | values |", "|---|---|"]
    lines += [f"| {k} | {fmt(Counter(c))} |" for k, c in v["key_codes_a"].items()]
    lines += ["", f"**Agreement** (n = {cov['shared']}):", "", "| field | agreement | kappa | flag | note |", "|---|---|---|---|---|"]
    for r in v["agreement"]:
        flag = "UNRELIABLE" if r["kappa"] < 0.6 else ""
        lines.append(f"| {r['field']} | {r['agreement']:.0%} | {r['kappa']:.2f} | {flag} | {r.get('note', '')} |")
    lines += ["", "Ricky's cross-tabs of the disagreements (A's code first) are in `results/village/AGREEMENT.md`.", ""]
    return lines


def sensitivity_section(sens):
    lines = ["What-if checks, not results: proposal P1 in `battery/v0.6-proposed.md` (the reporting channel becomes metadata, "
             "so `no_channel_provided` and the `no_channel` break leave the coder's values) applied to the existing codes.", "",
             "| dataset | field | v0.5: agreement / kappa | with P1: agreement / kappa |", "|---|---|---|---|"]
    for ds, checks in sens.items():
        for field, (before, after) in checks.items():
            show = lambda st: f"{st[1]:.0%} / {'n/a' if st[2] is None else f'{st[2]:.2f}'}"
            lines.append(f"| {ds} | {field} | {show(before)} | {show(after)} |")
    lines += ["", "Raw agreement rises sharply while kappa stays low: once nearly every chunk has one value, kappa has no variation "
              "to measure (the prevalence paradox). P1 removes a real disagreement; kappa cannot show that on these samples.", ""]
    return lines


def render(runs, ep_rows, agree, village=None, sens=None):
    out = [
        "# Analysis (battery v0.5, frozen): wiki, HF and AI Village", "",
        "Generated by `src/analyze.py` from the coder outputs. Tables: `results/analysis/` "
        "(`codes_long.csv`, `episodes.csv`, `coverage.csv`, `agreement_<dataset>.csv`). Counts only; quote text stays out of git.",
        "Answers that failed validation (a quote not in the chunk, or an inference with no quote) are excluded from every count below.", "",
        "## Coverage", "", *coverage(runs, ep_rows), "",
        "Refused = the model's safety stop declined the chunk. Refused chunks were not retried and are not coded.",
        "Refusals are probably not random (technical content triggers them), so coded chunks under-represent the most technical pages.", "",
        "## Validation failures per question (answers dropped)", "", *validation(runs), "",
        "## Chain verdict", "",
        "`first_break` is recomputed from the validated chain (a step whose quotes failed counts as not observed).", "",
        "Episode level uses the merge rule in `battery/questions.md`: an observed value in any chunk beats `not_observable`, "
        "different observed values give `mixed`.", "", *chain_tables(runs, ep_rows),
        "## Key codes (valid answers, chunk level)", "", *key_codes(runs), "",
        "## Agreement between coders", "",
        "Cohen's kappa per field; fields with kappa < 0.6 are flagged UNRELIABLE. When nearly every chunk has the same value, "
        "kappa is unstable: read it together with raw agreement and the number of values seen. "
        "Agreement is computed only where at least 10 chunks were coded by both coders (not HF).", "", *agreement_tables(agree),
        *(["## AI Village (Ricky)", "", *village_section(village)] if village else []),
        *(["## Sensitivity: proposal P1", "", *sensitivity_section(sens)] if sens else []),
        "## Limits", "",
        "- collusion.wiki is mostly English, not German. Wiki shows public speech only; Judge, Own and Know how are rarely observable there.",
        "- The wiki sample is seeded: pages with >= 2 agents and >= 4 revisions, at most 10 chunks per page, pilot pages excluded, 300 chunks; 15% to the second coder.",
        "- HF is 5 investigator-selected chunks of the METR report. Claude coders refused most of them, so HF has one complete coder (OpenAI); no agreement for HF.",
        "- Coder A (Claude) and coder B (OpenAI) are from the same families as some of the agents being coded.",
        "- No human-coded gold set: agreement between coders is the only reliability evidence.",
        "- Village: coded via OpenRouter (provider pinned to Anthropic / OpenAI), not the vendors' APIs directly. Coder B's prompt had an extra "
        "chunk-id line and exact-quote reminder that coder A did not get. Control days are not verified calm "
        "(about 0.5 uncatalogued acts per room-day). Incident chunks are mostly the conversation around an act.",
        "- Village counts come from Ricky's summaries and include answers that failed validation; wiki/HF counts exclude them.", "",
    ]
    return "\n".join(out)
