#!/usr/bin/env python3
"""Append prompt and final AI response to one audit Markdown file."""
import argparse
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tool", required=True, help="Tool/model name actually used")
    parser.add_argument("--at", required=True, help="Original interaction ISO timestamp with timezone")
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--final-output", "--output", dest="output", type=Path, required=True,
                        help="File containing only the final user-visible response for this interaction")
    args = parser.parse_args()
    timestamp = datetime.fromisoformat(args.at)
    if timestamp.tzinfo is None:
        parser.error("Original interaction timestamp requires timezone")
    # Read both inputs first, so invalid files cannot partially append a report.
    prompt = args.prompt.read_text(encoding="utf-8")
    final_output = args.output.read_text(encoding="utf-8")
    if not prompt.strip() or not final_output.strip():
        parser.error("Prompt and final response must not be empty")
    report = ROOT / "audit/ai-audit.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    # Append only: preserve all human review already written into previous entries.
    lines = [] if report.exists() else ["# AI Audit Report", "", 'Declaration: "I use AI tools for the following tasks."', "",
             "For each interaction, retain the prompt and final user-visible AI response. Exclude internal reasoning, progress updates and tool traces.", ""]
    lines += [f"## {args.at} — {args.tool}", "", "### Prompt", "", prompt, "",
              "### Final AI response", "", final_output, "", "### Human review", "",
              "Pending: record actual corrections and reasoning.", ""]
    with report.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Appended prompt and final AI response to {report}; export audit/ai-audit.pdf after human review.")


if __name__ == "__main__":
    main()
