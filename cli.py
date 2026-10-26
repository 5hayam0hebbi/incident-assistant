"""cli.py - run the incident assistant from the terminal.

python cli.py triage samples/alert-db-pool.txt
python cli.py postmortem samples/incident-notes.txt --out postmortem.md
"""

import argparse
import sys

from assistant import postmortem, postmortem_markdown, triage, triage_markdown
from llm import AIError


def main() -> int:
    parser = argparse.ArgumentParser(description="AI incident assistant that runs on your laptop.")
    sub = parser.add_subparsers(dest="command", required=True)
    t = sub.add_parser("triage", help="summarize an alert and pull the matching runbook steps")
    t.add_argument("file", help="text file with the alert or log snippet")
    p = sub.add_parser("postmortem", help="draft a blameless postmortem from incident notes")
    p.add_argument("file", help="text file with timestamped incident notes")
    p.add_argument("--out", help="save the Markdown to this file")
    args = parser.parse_args()

    with open(args.file, encoding="utf-8") as f:
        text = f.read()
    try:
        if args.command == "triage":
            result, book = triage(text)
            output = triage_markdown(result, book)
        else:
            result, warnings = postmortem(text)
            output = postmortem_markdown(result)
            for w in warnings:
                print(f"WARNING: {w}", file=sys.stderr)
    except AIError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(output)
    if getattr(args, "out", None):
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Saved {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
