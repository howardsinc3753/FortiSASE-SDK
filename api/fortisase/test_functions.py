"""
Basic FUNCTION test — login, then hit two read-only monitor endpoints.

    pip install -r api/fortisase/requirements.txt
    python api/fortisase/test_functions.py

Creds load from ~/.config/fortisase/fortisase_credentials.yaml (OUTSIDE the repo).
Read-only GETs only. Never prints the password.
"""
import requests

from client import FortiSASEClient


def _shape(obj):
    """One-line shape of a JSON response so we can eyeball it without a wall of data."""
    if isinstance(obj, dict):
        return "{" + ", ".join(
            f"{k}:[{len(v)} items]" if isinstance(v, list) else f"{k}:{type(v).__name__}"
            for k, v in list(obj.items())[:10]) + "}"
    if isinstance(obj, list):
        return f"[{len(obj)} items]"
    return repr(obj)[:120]


def main():
    sase = FortiSASEClient.from_config()
    print(f"client_id={sase.client_id!r} api_id={str(sase.api_id)[:8]}…")

    print("1) login (OAuth token) …")
    sase.login()
    print("   [ok] access_token acquired\n")

    print("2) GET /monitor-api/v1/traffic-history?type=Outbound …")
    th = sase.get_traffic_history("Outbound")
    print("   [ok] 200 ·", _shape(th), "\n")

    print("3) GET /monitor-api/v1/user/vpn/sessions …")
    vs = sase.get_vpn_sessions()
    print("   [ok] 200 ·", _shape(vs))


if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as e:
        print(f"[fail] HTTP {e.response.status_code} · {e.response.text[:500]}")
    except Exception as ex:  # noqa: BLE001
        print(f"[fail] {type(ex).__name__}: {str(ex)[:500]}")
