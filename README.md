# Incident Assistant

[![ci](https://github.com/5hayam0hebbi/incident-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/5hayam0hebbi/incident-assistant/actions/workflows/ci.yml)

An AI helper for on-call engineers that runs entirely on your laptop. It does two jobs:

- **Triage:** reads an alert or log snippet, finds the matching runbook, and returns a severity, a plain-English summary, the likely cause, customer impact, the runbook steps to follow and what to check next.
- **Postmortem:** turns rough, timestamped incident notes into a blameless postmortem draft in Markdown: summary, impact, timeline, root cause, contributing factors, what went well and wrong, and owned action items.

The model runs locally through [Ollama](https://ollama.com) (Llama 3.2 by default), so alerts, logs and incident notes never leave your machine.

## Why I built it

I spent years leading production support and incident response for mission-critical banking applications. At 2 a.m. the first ten minutes go to finding the right runbook and working out who is affected, and the day after goes to turning messy bridge notes into a postmortem. This tool speeds up both, with one rule from regulated environments: **the AI may summarize, but it may not make things up.**

## Guardrails: how it avoids invented facts

| Risk | What the code does |
|---|---|
| The model answers in the wrong format | Every answer must match a fixed shape (`models.py`, checked by Pydantic). A broken answer gets one retry, then a clear error. |
| The model invents runbook steps | The runbook is chosen by plain word matching (`runbooks.py`), not by the AI. If no runbook matches, the steps list is emptied, whatever the model wrote. |
| The postmortem timeline invents times | Every timeline row whose time is not in your notes is dropped, with a warning printed for each one. |
| The postmortem blames people | The prompt asks for roles and teams, and the action-item shape has an `owner_role` field, never a person's name. |
| The model hangs or isn't running | Each call has a timeout (180 seconds by default) and a clear "is Ollama running?" message. |
| Results vary between runs | The first attempt runs at temperature 0 (most predictable answer). |

The output is always a **draft**. The postmortem says so at the top: review every line.

## How it works

```
alert.txt ──► runbooks.py: best word match ──► prompt (alert + runbook) ──► local LLM ──► Triage shape ──► Markdown
notes.txt ──► prompt (notes) ──► local LLM ──► Postmortem shape ──► drop rows with unknown times ──► Markdown
```

## Quick start

You need Python 3.12 or newer and Ollama.

1. **Install Ollama** from [ollama.com](https://ollama.com) and download the model (about 2 GB, first time only):
   ```bash
   ollama pull llama3.2
   ```
2. **Get the code and make a Python box for it.** A virtual environment (`.venv`) keeps this project's libraries separate from the rest of your computer:
   ```bash
   git clone https://github.com/5hayam0hebbi/incident-assistant.git
   cd incident-assistant
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
   Run `source .venv/bin/activate` again in every new terminal window.

## Usage

**Triage an alert:**

```bash
python cli.py triage samples/alert-db-pool.txt
```

The sample is a payments API with 4.8-second latency and "connection pool exhausted" errors. The assistant matches it to `runbooks/db-connection-pool.md` and prints:

```markdown
## Triage (SEV2)
<two-sentence summary>
**Likely cause:** ...
**Customer impact:** ...
### Runbook steps (from `runbooks/db-connection-pool.md`)
1. Check active connections on the database server against the pool maximum.
...
### Next checks
- ...
```

**Draft a postmortem:**

```bash
python cli.py postmortem samples/incident-notes.txt --out postmortem.md
```

The sample notes describe a bad deploy that leaked database connections, a restart that only helped for 9 minutes, and a rollback. The draft is printed and saved to `postmortem.md`. Any timeline row the model invented is listed as a `WARNING` and left out.

Exact wording changes from run to run; the structure and guardrails do not.

## Add your own runbooks

Drop a Markdown file into `runbooks/`. Use a clear title on the first line, the signs of the problem, and numbered steps:

```markdown
# Database connection pool exhausted

Signs: errors such as "connection pool exhausted" ...

1. Check active connections ...
2. ...
```

The matcher scores each runbook by how many meaningful words it shares with the alert, and needs at least 2 shared words to pick one. Included runbooks: database connection pool, expired certificate, disk full, memory-leak hang.

## Settings

Set these as environment variables (values your terminal passes to the program) to change defaults:

| Variable | Default | What it does |
|---|---|---|
| `INCIDENT_MODEL` | `llama3.2` | Which Ollama model to use, e.g. `INCIDENT_MODEL=llama3.1:8b` |
| `INCIDENT_TIMEOUT` | `180` | Seconds to wait for each answer |
| `OLLAMA_HOST` | `http://localhost:11434` | Where Ollama is running, if not on this machine |

Example: `INCIDENT_MODEL=llama3.1:8b python cli.py triage samples/alert-db-pool.txt`

## Tests and code quality

The tests use a fake model, so they run in seconds without Ollama:

```bash
pip install -r requirements-dev.txt
pytest -v
ruff check . && ruff format --check .
```

They cover runbook matching (right match, and no match for unrelated alerts), dropping runbook steps when no runbook matched, time handling such as `02:14` vs `2:14`, and removal of invented timeline rows. GitHub Actions runs linting and all tests on every push.

## Project layout

```
cli.py          command-line entry point (triage / postmortem)
assistant.py    prompts, guardrails and Markdown output
llm.py          the only file that talks to the model: timeout, retry, errors
models.py       the answer shapes the model must fill in
runbooks.py     loads runbooks and picks the best match, no AI
runbooks/       sample runbooks
samples/        sample alert and incident notes
tests/          pytest tests with a fake model
```

## Limitations

- A small local model can still word things poorly or misjudge severity. Treat the output as a first draft, not a decision.
- Runbook matching is simple word overlap. Clear runbook titles and signs make it work better.
- The timeline check verifies times, not the event text next to them.
- It reads text files only. It doesn't connect to PagerDuty, ServiceNow or a monitoring tool.
