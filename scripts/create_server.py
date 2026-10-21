#!/usr/bin/env python3
"""Create a server with an initial app.

DRY RUN BY DEFAULT: prints the payload and exits. Add --yes to actually launch
(this starts billing once your trial ends).

Field names follow Cloudways API v1 and are (verify) for v2: check the request
schema for POST /server in the API Playground (bodies are sent form-encoded; use
cw.post(..., as_json=True) if the Playground shows JSON). Valid provider/region/size
values come from the "Lists" endpoints, and they differ per provider.
"""
import argparse
import json

import cw


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--provider", required=True, help="e.g. do, vultr, linode, amazon, gce (verify)")
    p.add_argument("--region", required=True, help="provider-specific, e.g. nyc3")
    p.add_argument("--size", required=True, help="provider-specific instance type, e.g. 1GB")
    p.add_argument("--app", default="wordpress", help="application type, e.g. wordpress, laravel, phpstack")
    p.add_argument("--app-version", default="")
    p.add_argument("--server-label", default="hackathon-server")
    p.add_argument("--app-label", default="hackathon-app")
    p.add_argument("--project", default="")
    p.add_argument("--yes", action="store_true", help="really create the server")
    a = p.parse_args()

    payload = {
        "cloud": a.provider,
        "region": a.region,
        "instance_type": a.size,
        "application": a.app,
        "app_version": a.app_version,
        "server_label": a.server_label,
        "app_label": a.app_label,
        "project_name": a.project,
    }
    print("Payload:\n" + json.dumps(payload, indent=2))
    if not a.yes:
        print("\nDry run. Re-run with --yes to create.")
        return

    resp = cw.post("/server", payload)
    print("Response:", json.dumps(resp, indent=2))
    op_id = (resp.get("server") or {}).get("operations", [{}])[0].get("id") or resp.get("operation_id")
    if op_id:
        cw.wait_for_operation(op_id)
        print("Done. Run list_servers.py to see it.")
    else:
        print("No operation ID found in the response; check the dashboard for progress.")


if __name__ == "__main__":
    main()
