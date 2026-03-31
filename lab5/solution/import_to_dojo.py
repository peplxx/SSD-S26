#!/usr/bin/env python3
"""
Import SARIF scan reports to DefectDojo via its REST API.

Usage:
    python import_to_dojo.py [--url URL] [--user USER] [--password PASSWORD]
                             [--reports-dir DIR]

Defaults:
    --url      http://localhost:8080
    --user     admin
    --password (read from DOJO_PASSWORD env or prompted)
    --reports  ./reports
"""

import argparse
import json
import os
import sys
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Report manifest – (file, scan_type, product_name, tool)
# scan_type must match a value DefectDojo recognises for SARIF imports.
# DefectDojo accepts "SARIF" as a generic SARIF scan type.
# ---------------------------------------------------------------------------
SCAN_CONFIGS = [
    {
        "file": "bandit_vulpy.sarif",
        "scan_type": "SARIF",
        "product": "vulpy",
        "engagement": "SAST Bandit",
        "description": "Bandit SAST scan of the Vulpy Flask application",
    },
    {
        "file": "njsscan_dvna.sarif",
        "scan_type": "SARIF",
        "product": "dvna",
        "engagement": "SAST njsscan",
        "description": "njsscan SAST scan of the DVNA NodeJS application",
    },
    {
        "file": "flawfinder_dvca.sarif",
        "scan_type": "SARIF",
        "product": "dvca",
        "engagement": "SAST FlawFinder",
        "description": "FlawFinder SAST scan of the Damn Vulnerable C Program",
    },
]


# ---------------------------------------------------------------------------
# DefectDojo client
# ---------------------------------------------------------------------------
class DojoClient:
    def __init__(self, base_url: str, token: str):
        self.base = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Token {token}",
            }
        )

    # ------------------------------------------------------------------
    def _get_token(base_url: str, username: str, password: str) -> str:
        """Exchange credentials for an API token."""
        url = f"{base_url.rstrip('/')}/api/v2/api-token-auth/"
        resp = requests.post(url, data={"username": username, "password": password})
        resp.raise_for_status()
        token = resp.json().get("token")
        if not token:
            raise ValueError(f"No token in response: {resp.text}")
        print(f"  [auth] obtained API token for '{username}'")
        return token

    _get_token = staticmethod(_get_token)

    # ------------------------------------------------------------------
    def _get_or_create(self, list_url: str, create_url: str, name_field: str, name: str, extra: dict) -> int:
        """Return id of an existing object or create it."""
        params = {name_field: name}
        resp = self.session.get(list_url, params=params)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if results:
            obj_id = results[0]["id"]
            print(f"    found existing '{name}' (id={obj_id})")
            return obj_id

        payload = {name_field: name, **extra}
        resp = self.session.post(create_url, json=payload)
        resp.raise_for_status()
        obj_id = resp.json()["id"]
        print(f"    created '{name}' (id={obj_id})")
        return obj_id

    # ------------------------------------------------------------------
    def get_or_create_product(self, name: str, description: str = "") -> int:
        return self._get_or_create(
            list_url=f"{self.base}/api/v2/products/",
            create_url=f"{self.base}/api/v2/products/",
            name_field="name",
            name=name,
            extra={"description": description, "prod_type": 1},
        )

    def get_or_create_engagement(self, product_id: int, name: str, description: str = "") -> int:
        return self._get_or_create(
            list_url=f"{self.base}/api/v2/engagements/",
            create_url=f"{self.base}/api/v2/engagements/",
            name_field="name",
            name=name,
            extra={
                "product": product_id,
                "description": description,
                "target_start": "2026-01-01",
                "target_end": "2026-12-31",
                "engagement_type": "CI/CD",
                "status": "In Progress",
            },
        )

    # ------------------------------------------------------------------
    def import_scan(
        self,
        sarif_path: Path,
        scan_type: str,
        product_name: str,
        engagement_name: str,
        product_type_name: str = "Research and Development",
    ) -> dict:
        """Upload a SARIF file using the /import-scan/ endpoint."""
        url = f"{self.base}/api/v2/import-scan/"
        with sarif_path.open("rb") as fh:
            resp = self.session.post(
                url,
                data={
                    "scan_type": scan_type,
                    "product_name": product_name,
                    "product_type_name": product_type_name,
                    "engagement_name": engagement_name,
                    "auto_create_context": True,
                    "verified": False,
                    "active": True,
                    "close_old_findings": False,
                    "push_to_jira": False,
                },
                files={"file": (sarif_path.name, fh, "application/json")},
            )
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Import SARIF reports to DefectDojo")
    p.add_argument("--url", default="http://localhost:8080", help="DefectDojo base URL")
    p.add_argument("--user", default="admin", help="DefectDojo username")
    p.add_argument("--password", default=None, help="DefectDojo password (or set DOJO_PASSWORD)")
    p.add_argument(
        "--reports-dir",
        default=Path(__file__).parent / "reports",
        type=Path,
        help="Directory containing .sarif files",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    password = args.password or os.environ.get("DOJO_PASSWORD")
    if not password:
        import getpass
        password = getpass.getpass(f"DefectDojo password for '{args.user}': ")

    print(f"\n[*] Connecting to DefectDojo at {args.url}")
    token = DojoClient._get_token(args.url, args.user, password)
    client = DojoClient(args.url, token)

    success, failed = 0, 0

    for cfg in SCAN_CONFIGS:
        sarif_path = args.reports_dir / cfg["file"]
        print(f"\n[>>] Importing {cfg['file']}")

        if not sarif_path.exists():
            print(f"  [SKIP] File not found: {sarif_path}")
            failed += 1
            continue

        # Validate the file is non-empty JSON
        try:
            with sarif_path.open() as fh:
                data = json.load(fh)
            runs = data.get("runs", [])
            total_results = sum(len(r.get("results", [])) for r in runs)
            print(f"  [info] SARIF has {len(runs)} run(s), {total_results} result(s)")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  [WARN] Could not parse SARIF: {e}. Attempting import anyway ...")

        try:
            result = client.import_scan(
                sarif_path=sarif_path,
                scan_type=cfg["scan_type"],
                product_name=cfg["product"],
                engagement_name=cfg["engagement"],
                product_type_name="Research and Development",
            )
            test_id = result.get("test", {})
            if isinstance(test_id, dict):
                test_id = test_id.get("id", "?")
            findings = result.get("findings_count", "?")
            print(f"  [OK] Test id={test_id}, findings imported: {findings}")
            success += 1
        except requests.HTTPError as exc:
            print(f"  [ERROR] HTTP {exc.response.status_code}: {exc.response.text[:400]}")
            failed += 1

    print(f"\n{'='*60}")
    print(f" Import complete: {success} succeeded, {failed} failed")
    print(f"{'='*60}")
    print(f" Open http://localhost:8080 to view findings.")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
