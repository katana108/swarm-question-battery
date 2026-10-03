"""Build the full coder prompt for one chunk: instructions + questions + codebook + transcript.

Usage: python src/assemble_prompt.py data/village/pilot_in/p00.txt > prompt_p00.txt
Paste the output into any model (or send it through an API), save the JSON reply as pNN.json.
"""
import hashlib
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
BATTERY = ROOT / "battery"


def check_frozen(config_path=ROOT / "config.yaml"):
    """Refuse to run if a battery file differs from the frozen hashes in config.yaml."""
    frozen = yaml.safe_load(Path(config_path).read_text())["battery_sha256"]
    for name, expected in frozen.items():
        actual = hashlib.sha256((BATTERY / name).read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError(f"battery/{name} changed since the freeze; results would not be comparable")


def instructions():
    """The prompt block inside coder_prompt.md (the part between the ``` fences)."""
    text = (BATTERY / "coder_prompt.md").read_text()
    return re.search(r"```\n(.*?)\n```", text, re.S).group(1)


def assemble(chunk_text):
    return "\n\n".join(
        [
            instructions(),
            "=== QUESTIONS ===\n" + (BATTERY / "questions.md").read_text(),
            "=== CODEBOOK ===\n" + (BATTERY / "codebook.md").read_text(),
            "=== TRANSCRIPT CHUNK ===\n" + chunk_text,
            "Return one JSON object: chunk_id, answers (Q1..Q10), chain, first_break, unobserved_steps, surprises. JSON only.",
        ]
    )


if __name__ == "__main__":
    check_frozen()
    print(assemble(Path(sys.argv[1]).read_text()))
