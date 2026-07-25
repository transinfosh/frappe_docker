#!/usr/bin/env python3
"""准备并校验 Frappe 应用镜像的发布元数据。"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

VERSION_PATTERN = re.compile(
    r'^__version__\s*=\s*["\']([^"\']+)["\']\s*$', re.MULTILINE
)
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def normalize_repo(repo: str) -> str:
    repo = repo.strip()
    if repo.count("/") == 1 and "://" not in repo:
        return f"https://github.com/{repo}.git"
    return repo


def validate_tag(release_tag: str, version: str) -> None:
    if release_tag != f"v{version}":
        raise ValueError(f"发布标签 {release_tag} 与应用版本 {version} 不一致")


def load_version(version_file: Path) -> str:
    match = VERSION_PATTERN.search(version_file.read_text(encoding="utf-8"))
    if not match:
        raise ValueError(f"无法从 {version_file} 读取 __version__")
    return match.group(1)


def load_extra_apps(raw_json: str) -> list[dict[str, str]]:
    data = json.loads(raw_json or "[]")
    if not isinstance(data, list):
        raise ValueError("extra_apps_json 必须是 JSON 数组")

    result: list[dict[str, str]] = []
    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"第 {index} 个附加应用必须是 JSON 对象")

        url = normalize_repo(str(item.get("url", "")))
        branch = str(item.get("branch", "")).strip()
        commit = str(item.get("commit", "")).strip().lower()
        if not url or not branch or not COMMIT_PATTERN.fullmatch(commit):
            raise ValueError(
                f"第 {index} 个附加应用必须包含 url、branch 和 40 位 commit"
            )

        result.append({"url": url, "branch": branch, "commit": commit})
    return result


def git_auth_environment(token: str) -> dict[str, str]:
    environment = os.environ.copy()
    if not token:
        return environment

    credential = base64.b64encode(f"x-access-token:{token}".encode()).decode()
    environment.update(
        {
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "http.https://github.com/.extraheader",
            "GIT_CONFIG_VALUE_0": f"AUTHORIZATION: basic {credential}",
        }
    )
    return environment


def validate_dependency_locks(apps: list[dict[str, str]], token: str = "") -> None:
    environment = git_auth_environment(token)
    for app in apps:
        ref = f"refs/heads/{app['branch']}"
        result = subprocess.run(
            ["git", "ls-remote", app["url"], ref],
            check=True,
            capture_output=True,
            text=True,
            env=environment,
        )
        actual = result.stdout.partition("\t")[0].strip().lower()
        if actual != app["commit"]:
            name = Path(urlparse(app["url"]).path).stem
            raise ValueError(
                f"{name}:{app['branch']} 当前为 {actual or '不存在'}，"
                f"与锁定提交 {app['commit']} 不一致"
            )


def build_apps_json(
    app_repo: str,
    release_tag: str,
    extra_apps: list[dict[str, str]],
) -> list[dict[str, str]]:
    apps = [{"url": normalize_repo(app_repo), "branch": release_tag}]
    apps.extend({"url": app["url"], "branch": app["branch"]} for app in extra_apps)
    return apps


def write_github_output(path: Path, values: dict[str, str]) -> None:
    with path.open("a", encoding="utf-8") as output:
        for key, value in values.items():
            print(f"{key}={value}", file=output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-repo", required=True)
    parser.add_argument("--release-tag", required=True)
    parser.add_argument("--version-file", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--extra-apps-json", default="[]")
    parser.add_argument("--apps-json", type=Path, required=True)
    parser.add_argument("--github-output", type=Path, required=True)
    parser.add_argument("--source-token", default="")
    args = parser.parse_args()

    version = load_version(args.version_file)
    validate_tag(args.release_tag, version)
    extra_apps = load_extra_apps(args.extra_apps_json)
    validate_dependency_locks(extra_apps, args.source_token)

    apps = build_apps_json(args.app_repo, args.release_tag, extra_apps)
    args.apps_json.parent.mkdir(parents=True, exist_ok=True)
    args.apps_json.write_text(json.dumps(apps, indent=2) + "\n", encoding="utf-8")

    lock_material = json.dumps(
        {"source_sha": args.source_sha, "apps": extra_apps},
        sort_keys=True,
        separators=(",", ":"),
    )
    write_github_output(
        args.github_output,
        {
            "version": version,
            "source_sha": args.source_sha,
            "short_sha": args.source_sha[:12],
            "stable": str("-" not in version).lower(),
            "cache_bust": hashlib.sha256(lock_material.encode()).hexdigest(),
        },
    )


if __name__ == "__main__":
    main()
