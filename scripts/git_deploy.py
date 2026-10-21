#!/usr/bin/env python3
"""Deploy code to an app with Cloudways' Git integration.

Prereq: generate the app's deploy key in the dashboard (Deployment via Git) and
add it to your repo. The repo URL must be an SSH URL (git@host:org/repo.git).

Pull fields (server_id, app_id, git_url, branch_name, optional deploy_path) match
Cloudways' current webhook guide. The clone body is assumed to be the same
(verify in the API Playground).

  git_deploy.py clone --server 1 --app 2 --url git@github.com:me/r.git --branch main
  git_deploy.py pull  --server 1 --app 2 --url git@github.com:me/r.git --branch main
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
    p.add_argument("--url", required=True, help="SSH repo URL, e.g. git@github.com:org/repo.git")
    p.add_argument("--deploy-path", default="", help="subfolder of public_html (empty = public_html)")
    a = p.parse_args()

    if not a.url.startswith("git@"):
        raise SystemExit("--url must be an SSH URL: git@host:org/repo.git (HTTPS is not supported)")
    body = {"server_id": a.server, "app_id": a.app, "git_url": a.url, "branch_name": a.branch}
    if a.deploy_path:
        body["deploy_path"] = a.deploy_path

    resp = cw.post(f"/git/{a.action}", body)
    print(json.dumps(resp, indent=2))
    op_id = resp.get("operation_id") or (resp.get("operation") or {}).get("id")
    if op_id:
        cw.wait_for_operation(op_id)


if __name__ == "__main__":
    main()
