"""assistant.py - build the prompts, call the model, and check its answers against the source."""

import re

from llm import ask as ask_model
from models import Postmortem, Triage
from runbooks import Runbook, best_match, load

TRIAGE_PROMPT = """You are an experienced site reliability engineer on call.
Read the ALERT and the RUNBOOK. Fill in every field.
Rules: use only facts in the ALERT and RUNBOOK; never invent hosts, numbers or times.
runbook_steps must be steps copied from the RUNBOOK in order; if there is no runbook, leave it empty.

ALERT:
{alert}

RUNBOOK ({runbook_name}):
{runbook_text}
"""

POSTMORTEM_PROMPT = """You are writing a blameless postmortem from an engineer's incident notes.
Fill in every field. Rules: use only facts in the NOTES; copy each time exactly as written;
name roles or teams, never people; action items must prevent a repeat, not just restate the fix.

NOTES:
{notes}
"""


def triage(alert: str, books: list[Runbook] | None = None, ask=ask_model) -> tuple[Triage, Runbook | None]:
    """Summarize an alert and pull the matching runbook steps."""
    books = load() if books is None else books
    book = best_match(alert, books)
    prompt = TRIAGE_PROMPT.format(
        alert=alert.strip(),
        runbook_name=book.name if book else "none found",
        runbook_text=book.text if book else "(no matching runbook)",
    )
    result = ask(prompt, Triage)
    if book is None:
        result.runbook_steps = []  # guardrail: no runbook, so no steps can be real
    return result, book


def times_in(text: str) -> set[str]:
    """Every clock time in the text, like 02:14 or 2:14."""
    return {t.lstrip("0") or "0" for t in re.findall(r"\b\d{1,2}:\d{2}\b", text)}


def postmortem(notes: str, ask=ask_model) -> tuple[Postmortem, list[str]]:
    """Draft a postmortem; drop timeline rows whose time isn't in the notes, and say so."""
    result = ask(POSTMORTEM_PROMPT.format(notes=notes.strip()), Postmortem)
    allowed = times_in(notes)
    kept, warnings = [], []
    for entry in result.timeline:
        if times_in(entry.time) and times_in(entry.time) <= allowed:
            kept.append(entry)
        else:
            warnings.append(f"Dropped a timeline row with a time not in your notes: {entry.time} {entry.event}")
    result.timeline = kept
    return result, warnings


def triage_markdown(t: Triage, book: Runbook | None) -> str:
    source = f"`runbooks/{book.name}.md`" if book else "no matching runbook"
    steps = "\n".join(f"{i}. {s}" for i, s in enumerate(t.runbook_steps, 1)) or "_No runbook steps._"
    checks = "\n".join(f"- {c}" for c in t.next_checks)
    return (
        f"## Triage ({t.severity})\n\n{t.summary}\n\n**Likely cause:** {t.likely_cause}\n\n"
        f"**Customer impact:** {t.customer_impact}\n\n### Runbook steps (from {source})\n\n{steps}\n\n"
        f"### Next checks\n\n{checks}\n"
    )


def postmortem_markdown(p: Postmortem) -> str:
    def bullets(items):
        return "\n".join(f"- {i}" for i in items) or "- (none)"

    rows = "\n".join(f"| {e.time} | {e.event} |" for e in p.timeline)
    actions = "\n".join(f"| {a.priority} | {a.action} | {a.owner_role} |" for a in p.action_items)
    return (
        f"# {p.title}\n\n_Draft written by a local AI from incident notes. Review every line._\n\n"
        f"## Summary\n\n{p.summary}\n\n## Impact\n\n{p.impact}\n\n"
        f"## Timeline\n\n| Time | Event |\n|---|---|\n{rows}\n\n## Root cause\n\n{p.root_cause}\n\n"
        f"## Contributing factors\n\n{bullets(p.contributing_factors)}\n\n"
        f"## What went well\n\n{bullets(p.what_went_well)}\n\n## What went wrong\n\n{bullets(p.what_went_wrong)}\n\n"
        f"## Action items\n\n| Priority | Action | Owner |\n|---|---|---|\n{actions}\n"
    )
