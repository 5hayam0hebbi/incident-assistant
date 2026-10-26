from assistant import postmortem, postmortem_markdown, times_in, triage, triage_markdown
from models import ActionItem, Postmortem, TimelineEntry, Triage
from runbooks import Runbook, best_match, load


def fake_triage(prompt, shape):
    return Triage(
        summary="Payments API is slow.",
        likely_cause="Pool exhausted.",
        severity="SEV2",
        customer_impact="Transfers fail.",
        runbook_steps=["Restart the instance."],
        next_checks=["Check last deploy."],
    )


def test_best_match_finds_pool_runbook():
    alert = open("samples/alert-db-pool.txt").read()
    assert best_match(alert, load()).name == "db-connection-pool"


def test_best_match_none_when_unrelated():
    books = [Runbook("disk", "Disk full", "no space left on device")]
    assert best_match("cat pictures loading slowly", books) is None


def test_triage_uses_matched_runbook():
    alert = open("samples/alert-db-pool.txt").read()
    result, book = triage(alert, ask=fake_triage)
    assert book.name == "db-connection-pool"
    assert "runbooks/db-connection-pool.md" in triage_markdown(result, book)


def test_triage_without_runbook_drops_steps():
    result, book = triage("cat pictures loading slowly", books=[], ask=fake_triage)
    assert book is None and result.runbook_steps == []


def test_times_in_normalizes_leading_zero():
    assert times_in("at 02:14 and 2:31") == {"2:14", "2:31"}


def test_postmortem_drops_invented_times():
    notes = open("samples/incident-notes.txt").read()

    def fake(prompt, shape):
        return Postmortem(
            title="Payments latency",
            summary="s",
            impact="12% of transfers failed",
            timeline=[TimelineEntry(time="02:14", event="alert"), TimelineEntry(time="05:00", event="made up")],
            root_cause="connection leak",
            contributing_factors=[],
            what_went_well=[],
            what_went_wrong=[],
            action_items=[ActionItem(action="Add leak test", owner_role="Payments team", priority="P1")],
        )

    result, warnings = postmortem(notes, ask=fake)
    assert [e.time for e in result.timeline] == ["02:14"]
    assert len(warnings) == 1
    assert "| P1 | Add leak test | Payments team |" in postmortem_markdown(result)
