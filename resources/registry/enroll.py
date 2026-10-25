#!/usr/bin/env python3
"""Enable shared Registry credentials for a transinfosh application repository."""

import argparse
import json
import subprocess


def github(path: str) -> dict:
    return json.loads(subprocess.check_output(["gh", "api", path], text=True))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", help="transinfosh/<repository>")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Refresh existing Registry secrets after rotation",
    )
    args = parser.parse_args()
    if (
        not args.repository.startswith("transinfosh/")
        or args.repository.count("/") != 1
    ):
        parser.error(
            "Only repositories in the authorized transinfosh organization can be enrolled"
        )
    repository = github(f"repos/{args.repository}")
    organization = github("orgs/transinfosh")
    names = {"REGISTRY_USERNAME", "REGISTRY_PASSWORD"}
    organization_secrets = github("orgs/transinfosh/actions/secrets")
    inherited = {
        item["name"]
        for item in organization_secrets["secrets"]
        if item["visibility"] == "all"
    }
    if not names <= inherited:
        raise SystemExit(
            "Organization Registry secrets are missing or do not allow all repositories"
        )
    needs_repository_secrets = (
        repository["private"] and organization.get("plan", {}).get("name") == "free"
    )
    if not needs_repository_secrets:
        print(f"{args.repository}: uses organization Registry secrets")
        return
    existing = json.loads(
        subprocess.check_output(
            ["gh", "secret", "list", "--repo", args.repository, "--json", "name"],
            text=True,
        )
    )
    if names <= {item["name"] for item in existing} and not args.refresh:
        print(f"{args.repository}: repository Registry secrets already configured")
        return
    remote = (
        "sudo -n python3 -c 'import json; from pathlib import Path; "
        'd=json.loads(Path("/etc/registry/credentials/accounts.json").read_text()); '
        'print(json.dumps(d["push"]))\''
    )
    account = json.loads(
        subprocess.check_output(
            ["ssh", "-o", "BatchMode=yes", "adam@192.168.2.52", remote], text=True
        )
    )
    for name, value in (
        ("REGISTRY_USERNAME", account["username"]),
        ("REGISTRY_PASSWORD", account["password"]),
    ):
        subprocess.run(
            ["gh", "secret", "set", name, "--repo", args.repository],
            input=value,
            text=True,
            check=True,
        )
    print(
        f"{args.repository}: repository Registry secrets configured for GitHub Free private repository"
    )


if __name__ == "__main__":
    main()
