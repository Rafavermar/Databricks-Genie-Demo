"""Run allow-listed commands and write redacted evidence files."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
TOKEN_PATTERN = re.compile(
    r"(?i)(token|authorization|password|secret|cookie)([\"'=:\s]+)([^\s\",}]+)"
)

ALLOWED_COMMANDS = {
    "cli-version": ["databricks", "-v"],
    "bundle-validate": ["databricks", "bundle", "validate", "-o", "json"],
    "bundle-summary": ["databricks", "bundle", "summary", "-o", "json"],
}


def redact(text: str) -> str:
    """Remove email addresses and secret-like key/value strings."""
    text = EMAIL_PATTERN.sub("***@***", text)
    return TOKEN_PATTERN.sub(r"\1\2[REDACTED]", text)


def main() -> None:
    """Capture one allow-listed command."""
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence_name", choices=sorted(ALLOWED_COMMANDS))
    parser.add_argument("--profile", required=True)
    parser.add_argument("--output-dir", default="evidence")
    arguments = parser.parse_args()

    command = list(ALLOWED_COMMANDS[arguments.evidence_name])
    if arguments.evidence_name != "cli-version":
        command.extend(["--profile", arguments.profile])
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    output = redact((completed.stdout or "") + (completed.stderr or ""))
    payload = {
        "captured_at": datetime.now(UTC).isoformat(),
        "command": (
            " ".join([*command[:-2], "--profile", "<selected-profile>"])
            if arguments.evidence_name != "cli-version"
            else " ".join(command)
        ),
        "exit_code": completed.returncode,
        "output": output,
    }
    output_dir = Path(arguments.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{arguments.evidence_name}.json"
    output_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    if completed.returncode:
        raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
