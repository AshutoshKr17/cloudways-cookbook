#!/usr/bin/env python3
"""List your servers and their apps (read-only). Works with a Read-Only token."""
import cw


def main():
    data = cw.get("/server")
    servers = data.get("servers", [])
    if not servers:
        print("No servers found (or response shape differs; raw response below).")
        print(data)
        return
    for s in servers:
        print(f"[{s.get('id')}] {s.get('label')}  {s.get('cloud')}/{s.get('region')}  "
              f"{s.get('public_ip')}  status={s.get('status')}")
        for a in s.get("apps", []):
            print(f"    app {a.get('id')}: {a.get('label')} ({a.get('application')})")


if __name__ == "__main__":
    main()
