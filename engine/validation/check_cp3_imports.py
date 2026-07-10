"""CP3 static import gate - Phase 43 narrowed rule (Boundary 2).

Scans every .py file under engine/ and enforces, via AST (no imports are
executed):

  DENY, always:
    - any import of adapters.* or testing.*  (one-way seam: the engine must
      never import the bridge or the shadow pipeline)
    - any import under infrastructure.* that is NOT on the allowlist below
      (this covers deriv_adapter, demo_broker_adapter, mock_broker,
      transport, and anything execution-capable, present or future)

  ALLOW, narrowly:
    - infrastructure.broker.deriv.rest_shadow_adapter
    - infrastructure.broker.deriv.rest_transport
      ... but ONLY inside engine/feed/live_readonly.py, and ONLY lazily
      (never at module top level), so importing engine.* never touches
      broker code.

The check fails on execution CAPABILITY, not on legitimate data access.
Governed by docs/PHASE_43_BOUNDARY_AGREEMENT.md.

Run:  py -m engine.validation.check_cp3_imports
Exit: 0 = CP3 PASS, 1 = violations listed.
"""
from __future__ import annotations

import ast
import os
import sys

_ENGINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DENY_PREFIXES = ("adapters", "testing")
BROKER_PREFIX = "infrastructure"
ALLOWLIST = frozenset({
    "infrastructure.broker.deriv.rest_shadow_adapter",
    "infrastructure.broker.deriv.rest_transport",
})
# The only file permitted to use the allowlist, relative to engine/:
ALLOWED_FILE = os.path.join("feed", "live_readonly.py")


def _imports_in(tree: ast.AST):
    """Yield (module_name, lineno, is_top_level) for every import in the tree."""
    top_level_nodes = {
        id(n) for n in ast.iter_child_nodes(tree)
        if isinstance(n, (ast.Import, ast.ImportFrom))
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name, node.lineno, id(node) in top_level_nodes
        elif isinstance(node, ast.ImportFrom):
            if node.module:  # relative "from . import x" has module=None: internal
                yield node.module, node.lineno, id(node) in top_level_nodes


def check(engine_dir: str = _ENGINE_DIR):
    """Return (violations, allowed_uses); each entry is a printable string."""
    violations, allowed_uses = [], []
    for root, _dirs, files in os.walk(engine_dir):
        for name in sorted(files):
            if not name.endswith(".py"):
                continue
            path = os.path.join(root, name)
            rel = os.path.relpath(path, engine_dir)
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    tree = ast.parse(fh.read())
            except SyntaxError as e:
                violations.append(f"{rel}:{e.lineno}: does not parse: {e.msg}")
                continue
            for mod, lineno, top in _imports_in(tree):
                where = f"{rel}:{lineno}"
                if mod.split(".")[0] in DENY_PREFIXES:
                    violations.append(
                        f"{where}: FORBIDDEN import '{mod}' "
                        f"(one-way seam: engine must never import this)")
                elif mod == BROKER_PREFIX or mod.startswith(BROKER_PREFIX + "."):
                    if mod not in ALLOWLIST:
                        violations.append(
                            f"{where}: FORBIDDEN broker import '{mod}' "
                            f"(not on the Phase 43 read-data allowlist)")
                    elif rel != ALLOWED_FILE:
                        violations.append(
                            f"{where}: allowlisted import '{mod}' used OUTSIDE "
                            f"{ALLOWED_FILE} (only the live feed may use it)")
                    elif top:
                        violations.append(
                            f"{where}: allowlisted import '{mod}' at MODULE TOP "
                            f"LEVEL (must be lazy, inside connect())")
                    else:
                        allowed_uses.append(f"{where}: '{mod}' (lazy, allowlisted)")
    return violations, allowed_uses


def main() -> int:
    print("=" * 64)
    print("CP3 STATIC IMPORT GATE (Phase 43 narrowed rule)")
    print("=" * 64)
    violations, allowed_uses = check()
    if allowed_uses:
        print("Allowlisted read-data imports in use:")
        for line in allowed_uses:
            print("  " + line)
    else:
        print("Allowlisted read-data imports in use: none")
    print()
    if violations:
        print(f"CP3: FAIL ({len(violations)} violation(s))")
        for line in violations:
            print("  " + line)
        return 1
    print("CP3: PASS (read-data allowlist only; no execution-capable imports;")
    print("     no adapters.*/testing.* imports anywhere under engine/)")
    return 0


if __name__ == "__main__":
    sys.exit(main())