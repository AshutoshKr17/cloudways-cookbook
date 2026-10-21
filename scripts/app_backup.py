#!/usr/bin/env python3
"""Take an on-demand backup of one app (files + database) before you deploy.

Endpoint path and fields follow v1 (POST /app/manage/backup) and are (verify)
for v2 in the API Playground.

  app_backup.py --server 123 --app 456
"""
import argparse
import json

import cw


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--server", required=True)
    p.add_argument("--app", required=True)
    a = p.parse_args()

    resp = cw.post("/app/manage/backup", {"server_id": a.server, "app_id": a.app})
    print(json.dumps(resp, indent=2))
    op_id = resp.get("operation_id") or (resp.get("operation") or {}).get("id")
    if op_id:
        cw.wait_for_operation(op_id)
        print("Backup complete.")


if __name__ == "__main__":
    main()
