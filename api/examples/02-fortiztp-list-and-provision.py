#!/usr/bin/env python3
"""
List unprovisioned devices and provision an on-ramp via FortiZTP v2.

Reuses the working SDK at MSSP-SE-Tools/FortiZTP. Two on-ramp patterns:
  A) FortiAP / FortiExtender  -> provisionTarget="FortiSASE"        (FortiSASE-managed thin edge)
  B) FortiGate branch box     -> provisionTarget="FortiManagerCloud" (then FMG pushes the IPsec/SPA on-ramp template)

Daniel: run this yourself — it authenticates with your FortiCloud IAM creds.

Setup:
  pip install -r <FortiZTP>/requirements.txt
  export FORTIZTP_USERNAME=<apiId>  FORTIZTP_PASSWORD=<secret>
  # or pass --creds <credentials.yaml>
"""
import argparse, sys, os

# Point at the existing FortiZTP SDK (don't re-implement auth).
FORTIZTP_PKG = os.path.expanduser(
    r"~/Documents/Projects/MSSP-SE-Tools/FortiZTP"
)
sys.path.insert(0, FORTIZTP_PKG)

from fortiztp import FortiZTPClient  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="FortiZTP on-ramp provisioning")
    ap.add_argument("--creds", help="path to credentials.yaml (else uses env vars)")
    ap.add_argument("--serial", help="device serial to provision")
    ap.add_argument("--device-type", default="FortiGate",
                    choices=["FortiGate", "FortiAP", "FortiSwitch", "FortiExtender"])
    ap.add_argument("--pattern", choices=["A", "B"], default="B",
                    help="A=thin-edge->FortiSASE, B=FortiGate->FortiManagerCloud")
    ap.add_argument("--fmg-oid", type=int, help="FortiManager OID (pattern B)")
    ap.add_argument("--script-oid", type=int, help="bootstrap CLI script OID")
    ap.add_argument("--region", help="FortiCloud region (cloud targets)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    client = (FortiZTPClient.from_credential_file(args.creds)
              if args.creds else FortiZTPClient.from_env())

    # 1) Inventory: show what's waiting to be onboarded.
    unprov = client.list_devices(provision_status="unprovisioned")
    print(f"Unprovisioned devices: {len(unprov)}")
    for d in unprov:
        print(f"  {d.get('serial_number')}  {d.get('device_type')}  {d.get('platform','')}")

    if not args.serial:
        print("\n(no --serial given; inventory only)")
        return 0

    # 2) Build the provision call per pattern.
    if args.pattern == "A":
        # Thin edge (FortiAP/FortiExtender) straight to FortiSASE.
        # NOTE: the local SDK enum predates the FortiSASE target — see handoff/local-asset-inventory.md.
        # Until devices.py adds it, this documents the intended call:
        kwargs = dict(provision_target="FortiSASE", region=args.region)
    else:
        # FortiGate branch -> FortiManager Cloud, which then installs the on-ramp/SPA template.
        kwargs = dict(provision_target="FortiManager",
                      fortimanager_oid=args.fmg_oid, script_oid=args.script_oid)

    print(f"\nProvision {args.serial} ({args.device_type}) pattern {args.pattern}: {kwargs}")
    if args.dry_run:
        print("dry-run: not sending.")
        return 0

    result = client.provision_device(args.serial, args.device_type, **kwargs)
    print(result.get("message"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
