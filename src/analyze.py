"""Turn coder outputs into analysis tables: long-format codes, episode-level chains, refusals, agreement.

Usage: python src/analyze.py            # writes results/analysis/*.csv and results/ANALYSIS.md

Quote text is never written (raw data stays out of git); only closed codes, counts and ids.
Answers that fail validation (validate.py) are kept as rows with valid=0 and are left out of every count.
"""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from agreement import FIELDS, STEPS, cohen_kappa, labels
from validate import validate_result

ROOT = Path(__file__).parent.parent
OUT = ROOT / "results" / "analysis"
# (dataset, chunk folder, coder output folder); folders that do not exist yet (e.g. Village) are skipped
RUNS = [
    ("wiki", "data/wiki/main_in", "data/wiki/main_a"),
    ("wiki", "data/wiki/main_in", "data/wiki/main_b"),
    ("hf", "data/hf/pilot_in", "data/hf/main_a"),
    ("hf", "data/hf/pilot_in", "data/hf/main_b"),
    ("village", "data/village/main_in", "data/village/main_a"),
    ("village", "data/village/main_in", "data/village/main_b"),
]
MIN_SHARED = 10  # fewer chunks coded by both coders give no meaningful kappa
ABSENT = {"not_observable", "dropped", "None", None}


def load_run(dataset, in_dir, out_dir):
    """One dict per chunk in index.json: ids, coder, status, the result, and which labels failed validation."""
    in_dir, out_dir = ROOT / in_dir, ROOT / out_dir
    meta = json.loads((out_dir / "coder_meta.json").read_text())
    log = json.loads((out_dir / "cost_log.json").read_text()) if (out_dir / "cost_log.json").exists() else {"problems": {}}
    index = json.loads((in_dir / "index.json").read_text())
    ids = json.loads((in_dir / "second_coder_ids.json").read_text()) if meta["coder"] == "B" and (in_dir / "second_coder_ids.json").exists() else sorted(index)
    chunks = []
    for cid in ids:
        row = {"dataset": dataset, "coder": meta["coder"], "model": meta["model"], "chunk_id": cid,
               "episode_id": index[cid]["episode_id"], "result": None, "failed": set()}
        f = out_dir / f"{cid}.json"
        if f.exists():
            row["result"] = json.loads(f.read_text())
            text = (in_dir / f"{cid}.txt").read_text()
            row["failed"] = {label for label, ok, _ in validate_result(row["result"], text) if not ok}
            row["status"] = "coded"
        else:
            row["status"] = log["problems"].get(cid, "missing")
        chunks.append(row)
    return chunks


def long_rows(chunk):
    """Long format: one row per closed code value (lists and Q2/Q4/Q7 items give several rows)."""
    base = {k: chunk[k] for k in ("dataset", "episode_id", "chunk_id", "coder", "model")}
    for ans in chunk["result"].get("answers", []):
        q, valid = ans.get("q"), int(ans.get("q") not in chunk["failed"])
        extra = {"confidence": ans.get("confidence"), "observability": ans.get("observability"),
                 "n_quotes": len(ans.get("quotes") or []), "valid": valid}
        for field, value in (ans.get("code") or {}).items():
            if field == "items":
                for i, item in enumerate(value or []):
                    for k, v in item.items():
                        if k in ("condition", "reason", "first_by_type", "code", "how", "persists"):
                            yield base | {"question": q, "code_field": f"items[{i}].{k}", "code_value": v} | extra
            elif field == "noticed_by":
                for i, n in enumerate(value or []):
                    yield base | {"question": q, "code_field": f"noticed_by[{i}].notice", "code_value": n.get("notice")} | extra
            else:
                for v in value if isinstance(value, list) else [value]:
                    yield base | {"question": q, "code_field": field, "code_value": v} | extra
    for step, entry in (chunk["result"].get("chain") or {}).items():
        valid = int(f"chain:{step}" not in chunk["failed"])
        yield base | {"question": "chain", "code_field": step, "code_value": entry.get("value"),
                      "confidence": "", "observability": "", "n_quotes": len(entry.get("quotes") or []), "valid": valid}


def chain_values(chunk):
    """Chain step values of one chunk; steps whose quotes failed validation count as 'dropped'."""
    chain = chunk["result"].get("chain") or {}
    return {s: "dropped" if f"chain:{s}" in chunk["failed"] else str(chain.get(s, {}).get("value")) for s in STEPS}


def merge_step(values):
    """Episode rule (questions.md): an observed value beats not_observable; different observed values give mixed."""
    observed = {v for v in values if v not in ABSENT}
    if not observed:
        return "not_observable"
    return observed.pop() if len(observed) == 1 else "mixed"


def first_break(chain):
    """First step coded no (none for act); no_channel_provided gives no_channel; not_observable steps are skipped."""
    for step in STEPS:
        v = chain[step]
        if v == "no" or (step == "act" and v == "none"):
            return step
        if v == "no_channel_provided":
            return "no_channel"
        if v == "mixed":
            return "mixed"
    return "none"


def episodes(chunks):
    by_ep = defaultdict(list)
    for c in chunks:
        if c["result"] is not None:
            by_ep[c["episode_id"]].append(chain_values(c))
    rows = []
    for ep, chains in sorted(by_ep.items()):
        merged = {s: merge_step([ch[s] for ch in chains]) for s in STEPS}
        rows.append({"episode_id": ep, "n_chunks": len(chains), **merged, "first_break": first_break(merged)})
    return rows


def agreement(chunks_a, chunks_b):
    """Kappa per field on chunks both coders coded; answers that failed validation for either coder are left out."""
    a = {c["chunk_id"]: c for c in chunks_a if c["result"] is not None}
    b = {c["chunk_id"]: c for c in chunks_b if c["result"] is not None}
    shared = sorted(set(a) & set(b))
    label_q = {label: q for label, q, _ in FIELDS} | {f"chain {s}": f"chain:{s}" for s in STEPS}
    rows = []
    for field in [l for l, _, _ in FIELDS] + [f"chain {s}" for s in STEPS] + ["first_break"]:
        pairs = [(labels(a[i]["result"])[field], labels(b[i]["result"])[field]) for i in shared
                 if label_q.get(field) not in a[i]["failed"] | b[i]["failed"]]
        xs, ys = [p[0] for p in pairs], [p[1] for p in pairs]
        k = cohen_kappa(xs, ys)
        rows.append({"field": field, "n": len(pairs), "agreement": round(sum(x == y for x, y in pairs) / len(pairs), 3) if pairs else None,
                     "kappa": None if k is None else round(k, 3), "values_seen": len(set(xs) | set(ys)),
                     "flag": "UNRELIABLE" if k is not None and k < 0.6 else ""})
    return rows, len(shared)


def write_csv(path, rows):
    if not rows:
        return
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    from analysis_report import render

    OUT.mkdir(parents=True, exist_ok=True)
    runs = [load_run(*r) for r in RUNS if (ROOT / r[2] / "coder_meta.json").exists()]
    write_csv(OUT / "codes_long.csv", [row for chunks in runs for c in chunks if c["result"] for row in long_rows(c)])
    write_csv(OUT / "coverage.csv", [{k: c[k] for k in ("dataset", "coder", "model", "chunk_id", "episode_id", "status")} for chunks in runs for c in chunks])
    ep_rows = [{"dataset": ch[0]["dataset"], "coder": ch[0]["coder"], "model": ch[0]["model"], **e} for ch in runs for e in episodes(ch)]
    write_csv(OUT / "episodes.csv", ep_rows)
    agree = {}
    by_ds = defaultdict(dict)
    for chunks in runs:
        by_ds[chunks[0]["dataset"]][chunks[0]["coder"]] = chunks
    for ds, coders in by_ds.items():
        if {"A", "B"} <= set(coders):
            rows, n = agreement(coders["A"], coders["B"])
            if n >= MIN_SHARED:
                agree[ds] = (rows, n)
                write_csv(OUT / f"agreement_{ds}.csv", rows)
    (ROOT / "results" / "ANALYSIS.md").write_text(render(runs, ep_rows, agree))
    print(f"wrote {OUT} and results/ANALYSIS.md")


if __name__ == "__main__":
    main()
