"""runbooks.py - find the runbook that best matches an alert (plain word overlap, no AI)."""

import re
from dataclasses import dataclass
from pathlib import Path

STOP = {"the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "is", "at", "by", "with", "from", "be"}


@dataclass
class Runbook:
    name: str  # file name without .md, e.g. "db-connection-pool"
    title: str
    text: str


def words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP and len(w) > 2}


def load(folder: str = "runbooks") -> list[Runbook]:
    books = []
    for path in sorted(Path(folder).glob("*.md")):
        text = path.read_text(encoding="utf-8")
        title = text.splitlines()[0].lstrip("# ").strip() if text else path.stem
        books.append(Runbook(path.stem, title, text))
    return books


def best_match(alert: str, books: list[Runbook], minimum: int = 2) -> Runbook | None:
    """The runbook sharing the most words with the alert; None if nothing shares `minimum` words."""
    alert_words = words(alert)
    scored = [(len(alert_words & words(b.title + " " + b.text)), b) for b in books]
    scored = [(score, b) for score, b in scored if score >= minimum]
    if not scored:
        return None
    return max(scored, key=lambda pair: pair[0])[1]
