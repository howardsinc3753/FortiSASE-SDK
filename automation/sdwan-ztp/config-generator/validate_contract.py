#!/usr/bin/env python3
"""Contract validator (App side) — asserts the App's REAL CSV export matches
contract/roles-and-columns.yaml.

Two checks, both fail-loud (exit 1 with a diff):
  1. contract csv_columns (base + added, in order) == generator.fmg_headers_for()
     for every role  -> contract <-> real code
  2. contract meta_vars that carry a `csv:` field (filtered by applies_to) ==
     that role's csv_columns minus the 3 structural cols  -> catalog self-consistency

Run at CSV-export time and in CI. The FMG SDK ships the mirror of check #1/#2
against its adom-manifest.yaml.

    python validate_contract.py        # 0 = OK, 1 = drift
"""
import os
import sys
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
CONTRACT = os.path.join(HERE, "contract", "roles-and-columns.yaml")
STRUCTURAL = ["Serial Number", "Device Blueprint", "Name"]


def _load_generator():
    spec = importlib.util.spec_from_file_location("generator", os.path.join(HERE, "generator.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _role_flags(app_key):
    return {"role": app_key["role"], "dual_wan": bool(app_key.get("dual_wan"))}


def main():
    try:
        import yaml
    except ImportError:
        print("PyYAML required: pip install pyyaml", file=sys.stderr)
        return 2

    with open(CONTRACT, encoding="utf-8") as fh:
        c = yaml.safe_load(fh)
    gen = _load_generator()

    roles = {r["id"]: r for r in c["roles"]}
    base_cols = roles["bor-single"]["csv_columns"]
    meta = c["meta_vars"]
    errors = []

    for rid, r in roles.items():
        flags = _role_flags(r["app_key"])
        is_dual = flags["dual_wan"]
        is_spa = flags["role"] == "bor-spa"

        # ---- check 1: contract columns == real generator output ----
        expected = list(base_cols) + list(r.get("csv_columns_added", []))
        actual = gen.fmg_headers_for(flags)
        if expected != actual:
            only_c = [x for x in expected if x not in actual]
            only_g = [x for x in actual if x not in expected]
            errors.append(
                f"[{rid}] contract vs generator.fmg_headers_for MISMATCH\n"
                f"        contract-only: {only_c or '-'}\n"
                f"        code-only:     {only_g or '-'}\n"
                f"        order-diff:    {'yes' if sorted(expected)==sorted(actual) and expected!=actual else 'no'}"
            )

        # ---- check 2: catalog per-role csv fields == columns (minus structural) ----
        def applies(mv):
            a = mv.get("applies_to", "all")
            return a == "all" or (a == "dual" and is_dual) or (a == "spa" and is_spa)

        cat_cols = {m["csv"] for name, m in meta.items() if m.get("csv") and applies(m)}
        col_cols = {x for x in expected if x not in STRUCTURAL}
        if cat_cols != col_cols:
            miss = col_cols - cat_cols   # column with no catalog entry
            extra = cat_cols - col_cols  # catalog says column, but not in list
            errors.append(
                f"[{rid}] catalog vs csv_columns MISMATCH\n"
                f"        column-without-catalog-var: {sorted(miss) or '-'}\n"
                f"        catalog-var-not-in-columns: {sorted(extra) or '-'}"
            )

    if errors:
        print("CONTRACT DRIFT:\n" + "\n".join(errors), file=sys.stderr)
        return 1

    counts = {rid: len(base_cols) + len(r.get("csv_columns_added", [])) for rid, r in roles.items()}
    print("contract OK — App export matches contract for all roles.")
    print("  column counts: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
