#!/usr/bin/env python3
"""Prepare immutable metadata for a shared Frappe framework base image."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from prepare_release import (
    load_extra_apps,
    validate_dependency_locks,
    write_github_output,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--framework-apps-json", required=True)
    parser.add_argument("--apps-json", type=Path, required=True)
    parser.add_argument("--github-output", type=Path, required=True)
    parser.add_argument("--source-token", default="")
    args = parser.parse_args()

    framework_apps = load_extra_apps(args.framework_apps_json)
    if not framework_apps:
        raise ValueError("framework_apps_json 至少需要包含一个框架扩展应用")
    validate_dependency_locks(framework_apps, args.source_token)

    args.apps_json.parent.mkdir(parents=True, exist_ok=True)
    args.apps_json.write_text(
        json.dumps(
            [{"url": app["url"], "branch": app["branch"]} for app in framework_apps],
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    lock_material = json.dumps(framework_apps, sort_keys=True, separators=(",", ":"))
    write_github_output(
        args.github_output,
        {
            "cache_bust": hashlib.sha256(lock_material.encode()).hexdigest(),
        },
    )


if __name__ == "__main__":
    main()
