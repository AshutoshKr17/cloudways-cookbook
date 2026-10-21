"""Tiny Cloudways API client (standard library only).

Auth: Access Token via the CLOUDWAYS_TOKEN env var, sent as a Bearer token.
Base URL: CLOUDWAYS_API_BASE (default is the v2 base derived from Cloudways'
v1 -> v2 migration note; confirm it in https://developers.cloudways.com/docs).
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ.get("CLOUDWAYS_API_BASE", "https://api.cloudways.com/api/v2").rstrip("/")


def _token():
    tok = os.environ.get("CLOUDWAYS_TOKEN")
    if not tok:
        sys.exit("Set CLOUDWAYS_TOKEN (create one under Profile > API Integration).")
    return tok


def request(method, path, body=None, params=None):
    """Call the API and return parsed JSON. Exits with a readable error on failure."""
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {_token()}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:600]
        hint = {
            400: "token missing",
            401: "token invalid or expired",
            403: "token scope doesn't allow this call",
            422: "validation error: check field names/values against the Playground",
        }.get(e.code, "")
        sys.exit(f"HTTP {e.code} {hint}\n{detail}")
    except urllib.error.URLError as e:
        sys.exit(f"Network error: {e.reason}")


def get(path, **params):
    return request("GET", path, params=params or None)


def post(path, body):
    return request("POST", path, body=body)


def wait_for_operation(op_id, timeout=900, interval=10):
    """Poll an async operation until it finishes. Shape is a (verify) guess:
    expects {"operation": {"is_completed": "1"|1|true, "message": ...}}."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        op = get(f"/operation/{op_id}").get("operation", {})
        done = op.get("is_completed")
        print(f"  operation {op_id}: {op.get('message') or op.get('status') or 'running'}")
        if str(done).lower() in ("1", "true"):
            return op
        time.sleep(interval)
    sys.exit(f"Timed out waiting for operation {op_id}")
