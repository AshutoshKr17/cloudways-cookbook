"""Tiny Cloudways API client (standard library only).

Auth: Access Token via the CLOUDWAYS_TOKEN env var, sent as a Bearer token.
Base URL: CLOUDWAYS_API_BASE (default https://api.cloudways.com/api/v2, the v2 base
listed in Cloudways' MCP 2.0 announcement).

POST bodies are sent form-encoded, matching Cloudways' official Git webhook sample.
Pass as_json=True if an endpoint in the Playground expects JSON.
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


def request(method, path, body=None, params=None, as_json=False):
    """Call the API and return parsed JSON. Exits with a readable error on failure."""
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    if body is None:
        data, ctype = None, "application/json"
    elif as_json:
        data, ctype = json.dumps(body).encode(), "application/json"
    else:
        data, ctype = urllib.parse.urlencode(body).encode(), "application/x-www-form-urlencoded"
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {_token()}",
            "Accept": "application/json",
            "Content-Type": ctype,
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


def post(path, body, as_json=False):
    return request("POST", path, body=body, as_json=as_json)


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
