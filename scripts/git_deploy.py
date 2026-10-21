#!/usr/bin/env python3
"""Deploy code to an app with Cloudways' Git integration.

Prereq: generate the app's deploy key in the dashboard (Deployment via Git) and
add it to your repo. The repo URL must be an SSH URL (git@host:org/repo.git).

Endpoints/fields follow v1 and are (verify) for v2 in the API Playground.

  git_deploy.py clone --server 1 --app 2 --url git@github.com:me/r.git --branch main
  git_deploy.py pull  --server 1 --app 2 --branch main
"""
import argparse
import json

import cw


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("action", choices=["clone", "pull"])
    p.add_argument("--server", required=True)
    p.add_argument("--app", required=True)
    p.add_argument("--branch", required=True)
    p.add_argument("--url", help="SSH repo URL (clone only)")
    p.add_argument("--deploy-path", default="", help="subfolder of public_html (clone only)")
    a = p.parse_args()

    body = {"server_id": a.server, "app_id": a.app, "branch_name": a.branch}
    if a.action == "clone":
        if not a.url or not a.url.startswith("git@"):
            raise SystemExit("clone needs --url in SSH form: git@host:org/repo.git")
        body.update({"git_url": a.url, "deploy_path": a.deploy_path})

    resp = cw.post(f"/git/{a.action}", body)
    print(json.dumps(resp, indent=2))
    op_id = resp.get("operation_id") or (resp.get("operation") or {}).get("id")
    if op_id:
        cw.wait_for_operation(op_id)


if __name__ == "__main__":
    main()
