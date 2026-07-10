"""Phase 42.0C-slice — M0 engine regression net.

Self-contained regression test for the Phase 42.0B-M0 reference producer. Proves
the engine still emits the known-good signal, that the test actually detects
drift (negative test), and that production is deterministic.

ARCHITECTURE BOUNDARY (must hold): this module imports ONLY engine.* and the
standard library. It must NOT import testing.shadow.* or adapters.* — the engine
owns its own regression boundary and must not depend on the frozen pipeline it
emits into. CP4 (real bridge compatibility) is a SEPARATE, manual integration
check, intentionally not run here.

Run:  py -m engine.validation.test_m0_regression
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile

from engine.assemble.signal_builder import V1_FIELDS
from engine.runner import run_once

# Bridge-owned fields the engine must NOT emit (the frozen bridge injects these).
BRIDGE_OWNED_FIELDS = ("schema_version", "signal_id", "signal_hash")

# Direction vocabulary the engine is allowed to emit (self-contained copy; the
# engine does not import the contract's normalize_direction here, by design).
_ALLOWED_DIRECTIONS = {"long", "short", "buy", "sell"}

_HERE = os.path.dirname(os.path.abspath(__file__))
_GOLDEN_PATH = os.path.join(_HERE, "fixtures", "m0_signal_golden.json")
_SNAPSHOT = os.path.join(_HERE, "..", "output", "sample_snapshot.json")


def _load_golden() -> dict:
    with open(_GOLDEN_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _emit_to_temp() -> dict:
    """Run the engine to a TEMP output (never the real live_signals.jsonl) and
    return the single emitted signal dict. The temp file is removed."""
    fd, tmp = tempfile.mkstemp(suffix=".jsonl", prefix="m0_regress_")
    os.close(fd)
    try:
        os.remove(tmp)  # run_once appends; start from absent so we get exactly one line
        result = run_once(snapshot_path=_SNAPSHOT, output_path=tmp, symbol="R_100")
        with open(tmp, "r", encoding="utf-8") as fh:
            lines = [ln for ln in fh.read().splitlines() if ln.strip()]
        assert len(lines) == 1, f"expected exactly 1 emitted line, got {len(lines)}"
        on_disk = json.loads(lines[0])
        # the returned dict and the on-disk line must agree
        assert on_disk == result, "returned signal and on-disk signal differ"
        return on_disk
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def _validate_fields(sig: dict) -> list[str]:
    """Self-contained field/semantic checks. Returns a list of problems (empty = ok)."""
    problems: list[str] = []
    keys = set(sig.keys())
    expected = set(V1_FIELDS)
    missing = expected - keys
    extra = keys - expected
    bridge = keys & set(BRIDGE_OWNED_FIELDS)
    if missing:
        problems.append(f"missing fields: {sorted(missing)}")
    if extra:
        problems.append(f"unexpected fields: {sorted(extra)}")
    if bridge:
        problems.append(f"bridge-owned fields present: {sorted(bridge)}")
    # direction validity (self-contained — does not import the contract)
    if "direction" in sig and str(sig["direction"]).strip().lower() not in _ALLOWED_DIRECTIONS:
        problems.append(f"invalid direction: {sig['direction']!r}")
    # numeric coercibility for the numeric fields
    for f in ("timestamp", "score", "entry_price", "stop_loss", "take_profit",
              "risk_percent", "confidence"):
        if f in sig:
            try:
                float(sig[f])
            except (TypeError, ValueError):
                problems.append(f"non-numeric {f}: {sig[f]!r}")
    return problems


def _sig_hash(sig: dict) -> str:
    """Stable hash of a signal via canonical JSON (sorted keys)."""
    return hashlib.sha256(
        json.dumps(sig, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


# --------------------------------------------------------------------------- #
# Test 1 — positive regression
# --------------------------------------------------------------------------- #
def test_positive_regression() -> None:
    sig = _emit_to_temp()
    problems = _validate_fields(sig)
    assert not problems, f"emitted signal failed validation: {problems}"

    golden = _load_golden()
    # exact equality (serialized, sorted) — determinism was proven in M0
    assert _sig_hash(sig) == _sig_hash(golden), (
        "emitted signal does not match golden fixture.\n"
        f"  emitted: {json.dumps(sig, sort_keys=True)}\n"
        f"  golden : {json.dumps(golden, sort_keys=True)}"
    )
    print("  Test 1 (positive regression): PASS")


# --------------------------------------------------------------------------- #
# Test 2 — negative regression (proves the test has teeth)
# --------------------------------------------------------------------------- #
def test_negative_regression() -> None:
    golden = _load_golden()

    # mutation A: invalid direction must be caught by _validate_fields
    bad_dir = dict(golden)
    bad_dir["direction"] = "INVALID"
    assert _validate_fields(bad_dir), "invalid direction was NOT caught — net has no teeth"

    # mutation B: removing a required field must be caught
    missing_conf = dict(golden)
    del missing_conf["confidence"]
    assert _validate_fields(missing_conf), "missing confidence was NOT caught — net has no teeth"

    # mutation C: a value change must break the golden match (hash differs)
    changed_val = dict(golden)
    changed_val["score"] = golden["score"] + 1.0
    assert _sig_hash(changed_val) != _sig_hash(golden), "value change did not alter hash"

    print("  Test 2 (negative regression): PASS — drift is detected")


# --------------------------------------------------------------------------- #
# Test 3 — deterministic repeatability (captured-snapshot path ONLY)
# --------------------------------------------------------------------------- #
def test_determinism_snapshot_path() -> None:
    # Scoped to the deterministic captured-snapshot feed. The live feed (Phase 43)
    # produces changing timestamps by design and is NOT covered by this assertion.
    a = _emit_to_temp()
    b = _emit_to_temp()
    assert _sig_hash(a) == _sig_hash(b), "two snapshot-path runs produced different signals"
    print("  Test 3 (determinism, snapshot path): PASS")


def run() -> bool:
    print("=" * 60)
    print("Phase 42.0C-slice — M0 engine regression")
    print("=" * 60)
    failures = 0
    for fn in (test_positive_regression, test_negative_regression,
               test_determinism_snapshot_path):
        try:
            fn()
        except AssertionError as e:
            failures += 1
            print(f"  {fn.__name__}: FAIL — {e}")
        except Exception as e:  # a crash is also a failure — report it readably
            failures += 1
            print(f"  {fn.__name__}: FAIL (raised {type(e).__name__}) — {e}")
    print("-" * 60)
    if failures == 0:
        print("42.0C ENGINE REGRESSION: PASS (3/3)")
        print("42.0C bridge compatibility: run CP4 manually (separate gate):")
        print("  py -m testing.shadow.signal_bridge_check --journal .\\engine\\output\\live_signals.jsonl")
    else:
        print(f"42.0C ENGINE REGRESSION: FAIL ({failures} test(s) failed)")
    print("=" * 60)
    return failures == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if run() else 1)
