from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid


def _request(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    json_body: dict | None = None,
    form_body: dict[str, str] | None = None,
    timeout: float = 5.0,
) -> tuple[int, dict[str, str], str]:
    data = None
    req_headers = dict(headers or {})

    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        req_headers["Content-Type"] = "application/json"

    if form_body is not None:
        data = urllib.parse.urlencode(form_body).encode("utf-8")
        req_headers["Content-Type"] = "application/x-www-form-urlencoded"

    req = urllib.request.Request(url, method=method, headers=req_headers, data=data)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, dict(resp.headers.items()), body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return int(e.code), dict(e.headers.items()), body


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def main() -> int:
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

    # 1) Health (legacy)
    code, headers, body = _request("GET", f"{base_url}/health")
    _assert(code == 200, f"/health expected 200, got {code}")
    _assert(body.strip() == '{"status":"ok"}', f"/health body mismatch: {body!r}")
    _assert(
        "x-request-id" in {k.lower() for k in headers.keys()},
        "missing X-Request-ID",
    )

    # 2) Readiness (v1)
    code, _headers, body = _request("GET", f"{base_url}/api/v1/health/ready")
    _assert(code == 200, f"/api/v1/health/ready expected 200, got {code} body={body!r}")

    # 3) Standard error schema (404)
    code, headers, body = _request("GET", f"{base_url}/api/v1/does-not-exist")
    _assert(code == 404, f"expected 404, got {code}")
    parsed = json.loads(body)
    _assert("error" in parsed, f"expected error wrapper, got {parsed}")
    _assert(parsed["error"]["code"] == "not_found", f"wrong code: {parsed['error']}")
    _assert(parsed["error"]["request_id"], "missing error.request_id")
    _assert(
        headers.get("X-RateLimit-Limit") or headers.get("x-ratelimit-limit"),
        "missing rate limit headers (enabled?)",
    )

    # 4) Create user (v1) + login (legacy)
    email = f"verify-{uuid.uuid4()}@example.com"
    code, _headers, body = _request(
        "POST",
        f"{base_url}/api/v1/users",
        json_body={"email": email, "password": "pass123"},
    )
    _assert(code == 201, f"expected 201 create user, got {code} body={body!r}")
    user_id = json.loads(body)["id"]

    code, _headers, body = _request(
        "POST",
        f"{base_url}/auth/login",
        form_body={"username": email, "password": "pass123"},
    )
    _assert(code == 200, f"expected 200 login, got {code} body={body!r}")
    token = json.loads(body)["access_token"]

    # 5) Cache demo: GET /api/v1/users/{id} twice (server-side cache)
    auth_headers = {"Authorization": f"Bearer {token}"}
    code, _headers, body1 = _request(
        "GET", f"{base_url}/api/v1/users/{user_id}", headers=auth_headers
    )
    _assert(code == 200, f"expected 200 get user, got {code} body={body1!r}")
    code, _headers, body2 = _request(
        "GET", f"{base_url}/api/v1/users/{user_id}", headers=auth_headers
    )
    _assert(code == 200, f"expected 200 get user (2nd), got {code} body={body2!r}")

    # 6) Rate limiting: hit a v1 path until we see 429 (configured to 60 in env.example)
    hit_429 = False
    for i in range(1, 80):
        code, headers, body = _request("GET", f"{base_url}/api/v1/does-not-exist")
        if code == 429:
            hit_429 = True
            parsed = json.loads(body)
            _assert(
                parsed["error"]["code"] == "rate_limited",
                "expected rate_limited code",
            )
            _assert(
                headers.get("X-RateLimit-Reset") or headers.get("x-ratelimit-reset"),
                "missing X-RateLimit-Reset",
            )
            break
        time.sleep(0.02)

    _assert(hit_429, "did not hit 429 within 80 requests (is rate limiting enabled?)")

    print("OK: prod hardening verification passed against", base_url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
