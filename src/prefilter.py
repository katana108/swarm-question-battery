"""Plain-code prefilter: keyword hits per episode, no model involved.

Used to pick chunks and to report raw counts. Hits are leads, not findings:
a word like "user" appears in many technical pages that are not about humans.
"""
import re
from collections import Counter

# From the handoff (section 6, step 3).
HUMAN_WORDS = ["human", "operator", "admin", "moderator", "staff", "user", "email", "report", "help@"]

# TODO(human): fill these three lists with the words you would look for.
MORAL_WORDS = []  # words that label an act as wrong, e.g. "unethical"
TECHNICAL_WORDS = []  # neutral or technical labels for the same act, e.g. "workaround"
OBJECTION_WORDS = []  # words an agent uses to object to another agent, e.g. "stop"

CATEGORIES = {
    "human": HUMAN_WORDS,
    "moral": MORAL_WORDS,
    "technical": TECHNICAL_WORDS,
    "objection": OBJECTION_WORDS,
}


def _pattern(words):
    if not words:
        return None
    return re.compile("|".join(re.escape(w) for w in words), re.IGNORECASE)


def count_hits(text, categories=None):
    """Count keyword hits per category in a text. Empty word lists count as zero."""
    counts = Counter()
    for name, words in (categories or CATEGORIES).items():
        pat = _pattern(words)
        counts[name] = len(pat.findall(text)) if pat else 0
    return counts


def episode_hits(episodes, categories=None):
    """episodes: {episode_id: [rows]} -> {episode_id: Counter of hits}."""
    return {
        eid: sum((count_hits(r["text"], categories) for r in rows), Counter())
        for eid, rows in episodes.items()
    }


def summarize(hits):
    """Raw counts for the report: number of episodes with at least one hit, per category."""
    return {name: sum(1 for c in hits.values() if c[name] > 0) for name in CATEGORIES}
