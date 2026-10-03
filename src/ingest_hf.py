"""Ingest the METR Hugging Face incident report into page-based chunks.

The raw transcripts are not public, so the "transcript" is the report itself:
investigators' prose with agent quotes embedded ({curly braces} = paraphrase).
All results from it are an investigator-selected sample; do not compute rates.
"""
import re
import sys
from pathlib import Path

from pypdf import PdfReader

MAX_CHARS = 24000
QUOTE_MARKS = re.compile(r"\{[^}]{10,}\}|“[^”]{10,}”")


def read_pages(pdf_path):
    """Return {page_number: text}, whitespace collapsed (pypdf puts one word per line)."""
    reader = PdfReader(pdf_path)
    return {i: re.sub(r"\s+", " ", p.extract_text() or "").strip() for i, p in enumerate(reader.pages, 1)}


def chunk_pages(pages, max_chars=MAX_CHARS):
    """Pack whole pages into chunks; each page starts with a [page N] header so quotes can be cited."""
    chunks, current, size = [], [], 0
    for n, text in pages.items():
        block = f"[page {n}]\n{text}\n"
        if current and size + len(block) > max_chars:
            chunks.append(current)
            current, size = [], 0
        current.append((n, block))
        size += len(block)
    if current:
        chunks.append(current)
    return [
        {
            "chunk_id": f"hf#{i}",
            "episode_id": "hf",
            "pages": [n for n, _ in group],
            "text": "".join(b for _, b in group),
        }
        for i, group in enumerate(chunks)
    ]


def quote_density(chunk):
    return len(QUOTE_MARKS.findall(chunk["text"]))


if __name__ == "__main__":
    root = Path(__file__).parent.parent / "data" / "hf"
    chunks = chunk_pages(read_pages(root / "report.pdf"))
    for c in chunks:
        print(c["chunk_id"], f"pages {c['pages'][0]}-{c['pages'][-1]}", "quotes", quote_density(c), file=sys.stderr)
    out = root / "pilot_in"
    out.mkdir(exist_ok=True)
    top = sorted(chunks, key=quote_density, reverse=True)[: int(sys.argv[1]) if len(sys.argv) > 1 else 5]
    for c in sorted(top, key=lambda c: c["pages"][0]):
        (out / f"{c['chunk_id'].replace('#', '_')}.txt").write_text(c["text"])
        print("selected", c["chunk_id"], c["pages"][0], "-", c["pages"][-1])
