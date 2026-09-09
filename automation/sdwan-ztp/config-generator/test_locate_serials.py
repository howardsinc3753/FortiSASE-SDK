"""
QA test for locate_serials — pins the fail-fast contract on both source list calls.

Run:
    python automation/sdwan-ztp/config-generator/test_locate_serials.py

No live FMG needed — the two list functions are monkey-patched to return fixtures or raise
ToolError. Every assertion prints PASS/FAIL and the script exits non-zero on any failure.

Focus is finding F2: pre-fix, list_adom_devices ToolError was swallowed into set() and an
in-target serial got misclassified 'elsewhere'. Post-fix, either list call failing must raise.

(Test authored by FMG-SDK Claude / howar-a7; F1+F2 fold + integration by App Claude. Print
labels are ASCII so Windows cp1252 stdout renders cleanly.)
"""
import sys
import pathlib

# Import fmg_provision from this same folder.
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fmg_provision as fp  # noqa: E402


FAILS = 0


def check(label, cond, detail=""):
    global FAILS
    tag = "PASS" if cond else "FAIL"
    if not cond:
        FAILS += 1
    print(f"  [{tag}] {label}" + (f"  - {detail}" if detail else ""))


# ---------------------------------------------------------------------------
# Fixtures + monkey-patch helpers. Each test rebinds fp.list_adom_devices and
# fp.list_all_devices so the classifier operates on controlled inputs.
# ---------------------------------------------------------------------------

def _seed(adom_map, global_devices):
    """adom_map: {adom_name: [{name, sn, platform}, ...]}. global_devices: same shape flat list.
    Wire fp.list_adom_devices + fp.list_all_devices to return these fixtures."""
    def fake_list_adom(host, adom):
        return list(adom_map.get(adom, []))

    def fake_list_all(host):
        return list(global_devices)

    fp.list_adom_devices = fake_list_adom  # type: ignore[attr-defined]
    fp.list_all_devices = fake_list_all    # type: ignore[attr-defined]


def _seed_target_raises(exc, adom_map_others, global_devices):
    """Target-ADOM list raises; other ADOMs behave normally."""
    def fake_list_adom(host, adom):
        if adom == "TARGET":
            raise exc
        return list(adom_map_others.get(adom, []))

    def fake_list_all(host):
        return list(global_devices)

    fp.list_adom_devices = fake_list_adom  # type: ignore[attr-defined]
    fp.list_all_devices = fake_list_all    # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Case 1 - Happy path. All 3 classifications reachable.
# ---------------------------------------------------------------------------
def test_happy_path():
    print("Case 1: happy path - new / in_target / elsewhere all classify correctly")
    # adom_list() is only consulted for elsewhere-name resolution; stub it too.
    fp.adom_list = lambda host: {"adoms": [                              # type: ignore[attr-defined]
        {"name": "TARGET", "device_count": 1},
        {"name": "OTHER",  "device_count": 1},
    ]}
    _seed(
        adom_map={
            "TARGET": [{"name": "spoke-1", "sn": "SN-IN-TARGET"}],
            "OTHER":  [{"name": "spoke-x", "sn": "SN-ELSEWHERE"}],
        },
        global_devices=[
            {"name": "spoke-1", "sn": "SN-IN-TARGET"},
            {"name": "spoke-x", "sn": "SN-ELSEWHERE"},
        ],
    )
    out = fp.locate_serials("fmg.example.com", ["SN-IN-TARGET", "SN-ELSEWHERE", "SN-NEW"], "TARGET")
    check("in-target classified", out["SN-IN-TARGET"] == {"state": "in_target", "adom": "TARGET"},
          detail=repr(out["SN-IN-TARGET"]))
    check("elsewhere classified + named", out["SN-ELSEWHERE"] == {"state": "elsewhere", "adom": "OTHER"},
          detail=repr(out["SN-ELSEWHERE"]))
    check("new classified", out["SN-NEW"] == {"state": "new", "adom": None},
          detail=repr(out["SN-NEW"]))


# ---------------------------------------------------------------------------
# Case 2 - F2 REGRESSION GUARD. Target-ADOM list fails; MUST raise, MUST NOT
# swallow into set() and misclassify. Pre-fix this returned
# {'SN-IN-TARGET': {'state': 'elsewhere', 'adom': None}}.
# ---------------------------------------------------------------------------
def test_target_adom_list_failure_propagates():
    print("Case 2 (F2 guard): target-ADOM list ToolError propagates instead of misclassifying")
    _seed_target_raises(
        exc=fp.ToolError("FMG blip: target-ADOM list transient error"),
        adom_map_others={"OTHER": []},
        global_devices=[{"name": "spoke-1", "sn": "SN-IN-TARGET"}],
    )
    raised = None
    try:
        fp.locate_serials("fmg.example.com", ["SN-IN-TARGET"], "TARGET")
    except fp.ToolError as e:
        raised = e
    check("ToolError raised (not swallowed)", raised is not None,
          detail="expected ToolError from list_adom_devices to propagate")
    check("error message identifies the source", raised is not None and "target-ADOM" in str(raised),
          detail=f"got: {raised!r}")


# ---------------------------------------------------------------------------
# Case 3 - Global DVM list fails; also raises (asymmetry check already existed;
# pin it so nobody reintroduces a symmetric swallow either way).
# ---------------------------------------------------------------------------
def test_global_dvm_list_failure_propagates():
    print("Case 3: global DVM list ToolError propagates too (asymmetry pin)")

    def fake_list_adom(host, adom):
        return [{"name": "spoke-1", "sn": "SN-IN-TARGET"}] if adom == "TARGET" else []

    def fake_list_all(host):
        raise fp.ToolError("FMG blip: global device list transient error")

    fp.list_adom_devices = fake_list_adom  # type: ignore[attr-defined]
    fp.list_all_devices = fake_list_all    # type: ignore[attr-defined]

    raised = None
    try:
        fp.locate_serials("fmg.example.com", ["SN-IN-TARGET"], "TARGET")
    except fp.ToolError as e:
        raised = e
    check("ToolError raised on global list failure", raised is not None,
          detail=f"got: {raised!r}")


# ---------------------------------------------------------------------------
# Case 4 - Empty-serials fast path (still short-circuits without any FMG call).
# ---------------------------------------------------------------------------
def test_empty_serials_no_fmg_calls():
    print("Case 4: empty serials short-circuits (no FMG calls made)")
    calls = {"adom": 0, "all": 0}

    def fake_list_adom(host, adom):
        calls["adom"] += 1
        return []

    def fake_list_all(host):
        calls["all"] += 1
        return []

    fp.list_adom_devices = fake_list_adom  # type: ignore[attr-defined]
    fp.list_all_devices = fake_list_all    # type: ignore[attr-defined]

    out = fp.locate_serials("fmg.example.com", [], "TARGET")
    check("empty result for empty input", out == {}, detail=repr(out))
    check("no FMG calls made", calls == {"adom": 0, "all": 0}, detail=repr(calls))
    # Blank strings + whitespace-only get filtered by str(s).strip().
    out = fp.locate_serials("fmg.example.com", ["", "   ", "\t"], "TARGET")
    check("empty result for all-blank input", out == {}, detail=repr(out))


# ---------------------------------------------------------------------------
# Case 5 - Non-target-ADOM naming scan tolerates per-ADOM failures (per-ADOM
# ToolError is still caught inside the naming loop; that's a separate contract
# from the top-level source lists).
# ---------------------------------------------------------------------------
def test_naming_scan_tolerates_per_adom_error():
    print("Case 5: naming-scan per-ADOM error is tolerated (unresolved stays unresolved)")
    fp.adom_list = lambda host: {"adoms": [                              # type: ignore[attr-defined]
        {"name": "TARGET", "device_count": 1},
        {"name": "FLAKY",  "device_count": 1},
        {"name": "OK",     "device_count": 1},
    ]}

    def fake_list_adom(host, adom):
        if adom == "TARGET":
            return []
        if adom == "FLAKY":
            raise fp.ToolError("FMG blip on this one ADOM")
        if adom == "OK":
            return [{"name": "spoke-x", "sn": "SN-ELSEWHERE"}]
        return []

    def fake_list_all(host):
        return [{"name": "spoke-x", "sn": "SN-ELSEWHERE"}]

    fp.list_adom_devices = fake_list_adom  # type: ignore[attr-defined]
    fp.list_all_devices = fake_list_all    # type: ignore[attr-defined]

    out = fp.locate_serials("fmg.example.com", ["SN-ELSEWHERE"], "TARGET")
    # Whichever order the two non-target ADOMs get scanned, the OK one still resolves the name.
    check("elsewhere resolved despite one ADOM error",
          out["SN-ELSEWHERE"] == {"state": "elsewhere", "adom": "OK"},
          detail=repr(out["SN-ELSEWHERE"]))


def main():
    tests = [
        test_happy_path,
        test_target_adom_list_failure_propagates,
        test_global_dvm_list_failure_propagates,
        test_empty_serials_no_fmg_calls,
        test_naming_scan_tolerates_per_adom_error,
    ]
    for t in tests:
        t()
        print()
    if FAILS:
        print(f"{FAILS} FAIL")
        sys.exit(1)
    print("all pass")


if __name__ == "__main__":
    main()
