"""Conservatively inspect one Databricks profile without exposing credentials."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class DetectionResult:
    """Sanitized workspace detection evidence."""

    profile: str
    authenticated: bool
    masked_host: str
    masked_identity: str
    cloud: str
    catalog_names: list[str]
    serverless_warehouse_count: int
    evidence: list[str]
    classification: str


def _run_json(arguments: list[str]) -> Any:
    completed = subprocess.run(
        ["databricks", *arguments, "-o", "json"],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def mask_host(host: str) -> str:
    """Mask the workspace-specific part of a Databricks hostname."""
    parsed = urlparse(host)
    labels = (parsed.hostname or "").split(".")
    if not labels:
        return "***"
    first = labels[0]
    masked_first = f"{first[:7]}***{first[-4:]}" if len(first) > 12 else "***"
    return f"{parsed.scheme or 'https'}://{masked_first}.{'.'.join(labels[1:])}"


def mask_identity(identity: str) -> str:
    """Mask an email-like identity."""
    if "@" not in identity:
        return "***"
    local, domain = identity.split("@", maxsplit=1)
    return f"{local[:2]}***@{domain}"


def _extract_host(profile: str) -> str:
    completed = subprocess.run(
        ["databricks", "auth", "describe", "--profile", profile],
        check=True,
        capture_output=True,
        text=True,
    )
    match = re.search(r"Host:\s+(https://\S+)", completed.stdout)
    return match.group(1) if match else ""


def detect(profile: str) -> DetectionResult:
    """Inspect authentication, workspace assets, and Free Edition signals."""
    user = _run_json(["current-user", "me", "--profile", profile])
    catalogs = _run_json(["catalogs", "list", "--profile", profile])
    warehouses = _run_json(["warehouses", "list", "--profile", profile])
    host = _extract_host(profile)
    serverless = [
        warehouse for warehouse in warehouses if warehouse.get("enable_serverless_compute")
    ]
    catalog_names = sorted(str(catalog["name"]) for catalog in catalogs)
    evidence: list[str] = []
    if host.endswith(".cloud.databricks.com"):
        evidence.append("AWS workspace hostname")
    if catalog_names == ["samples", "system", "workspace"]:
        evidence.append("single managed workspace catalog plus system catalogs")
    if len(serverless) == 1:
        evidence.append("one accessible serverless SQL warehouse")
    if any(warehouse.get("max_num_clusters") == 1 for warehouse in serverless):
        evidence.append("warehouse constrained to one cluster")
    classification = (
        "CONSISTENT_WITH_FREE_EDITION"
        if len(evidence) >= 3 and "workspace" in catalog_names
        else "INCONCLUSIVE"
    )
    return DetectionResult(
        profile=profile,
        authenticated=bool(user.get("active", True)),
        masked_host=mask_host(host),
        masked_identity=mask_identity(str(user.get("userName", ""))),
        cloud="AWS" if host.endswith(".cloud.databricks.com") else "unknown",
        catalog_names=catalog_names,
        serverless_warehouse_count=len(serverless),
        evidence=evidence,
        classification=classification,
    )


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    arguments = parser.parse_args()
    try:
        result = detect(arguments.profile)
    except subprocess.CalledProcessError as error:
        message = (error.stderr or error.stdout or str(error)).strip()
        raise SystemExit(f"Profile validation failed: {message}") from error
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
