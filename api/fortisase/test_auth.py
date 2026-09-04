"""
Basic auth smoke test — mint a FortiCloud OAuth token with the LAB creds.

    pip install requests pyyaml
    python api/fortisase/test_auth.py

Creds load from ~/.config/fortisase/fortisase_credentials.yaml (OUTSIDE the repo — never committed).
This ONLY proves config-plane auth (the IAM API user + client_id). It never prints the password.
"""
from client import FortiSASEClient   # same-dir import when run as: python api/fortisase/test_auth.py


def main():
    sase = FortiSASEClient.from_config()
    print(f"client_id = {sase.client_id!r} · api_id = {str(sase.api_id)[:8]}… · minting token @ IAM OAuth …")
    try:
        tok = sase.login()
        print(f"[ok] token received ({tok[:10]}…) — config-plane auth WORKS.")
        print("     Next: fill CONFIG_BASE from the FNDN Swagger, then try sase.list_fortigates().")
    except Exception as ex:  # noqa: BLE001
        print(f"[fail] {type(ex).__name__}: {str(ex)[:400]}")
        print("     Likely a TODO(swagger) item: client_id, grant_type/field names, or the token URL.")
        print("     (Or the lab creds — but you just minted them, so check the request shape first.)")


if __name__ == "__main__":
    main()
