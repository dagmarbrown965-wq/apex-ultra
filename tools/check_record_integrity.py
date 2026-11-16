"""Record-integrity checks for the APEX ULTRA repository.

Read-only. Standard library only. No network, no engine imports, no writes.

Two checks, both motivated by real failures found on 2026-11-16:

  1. DANGLING REFERENCES. Documents in docs/ cite repo-relative paths that do
     not exist. Found that day: docs/PHASE_42_1_BOUNDARY_AGREEMENT.md (cited by
     the Phase 42.1 handoff as a "locked five-point agreement", never existed in
     git) and tools/rest403_probe.py (recorded as Downloads-only, never
     committed, since lost). Also catches a sealed dataset going missing from
     engine/output/ -- see incident I1.

  2. AMENDMENT SEQUENCE GAPS. PHASE_<n>_AMENDMENT_V0_<m>.md families with a
     missing m. Amendment v0.6 was absent from docs/ for three months while
     v0.7 cited it and both Phase 48 seals claimed the chain was complete. The
     gap was visible in a directory listing the whole time.

WHAT THIS CANNOT DO: it cannot see the Claude project mirror, which lives on
claude.ai rather than the filesystem. It catches cited-but-absent and sequence
gaps. It does NOT catch a document written only in the mirror and never cited
from docs/. That residual needs a human step -- see PREFLIGHT.md.

Usage:  py -m tools.check_record_integrity
Exit:   0 clean, 1 findings, 2 could not run.
"""

import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(REPO_ROOT, "docs")
ALLOWLIST = os.path.join(REPO_ROOT, "tools", "known_absent.txt")

# Repo-relative paths worth checking. Deliberately includes engine/output:
# a sealed dataset disappearing is exactly what we want reported.
PATH_RE = re.compile(
    r"(?<![\w/\\.])"
    r"((?:docs|tools|engine|testing|infrastructure)"
    r"[/\\][A-Za-z0-9_./\\-]*"
    # jsonl BEFORE json: alternation is ordered, and "json" would otherwise
    # match first and truncate ".jsonl" to ".json". Caught by fixture test.
    r"\.(?:md|py|jsonl|json|txt|cfg|ini))"
)

AMENDMENT_RE = re.compile(r"^PHASE_(\d+)_AMENDMENT_V0_(\d+)\.md$")


def load_allowlist():
    """path -> reason, for gaps that are known and recorded."""
    known = {}
    if not os.path.isfile(ALLOWLIST):
        return known
    with open(ALLOWLIST, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "|" in line:
                path, reason = line.split("|", 1)
            else:
                path, reason = line, "(no reason recorded)"
            known[path.strip().replace("\\", "/")] = reason.strip()
    return known


def find_references():
    """{normalised path: sorted list of citing documents}"""
    refs = {}
    for name in sorted(os.listdir(DOCS_DIR)):
        if not name.endswith(".md"):
            continue
        full = os.path.join(DOCS_DIR, name)
        with open(full, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        # Markdown escapes underscores as \_ . Backslash is also our Windows
        # path separator, so without this a cited PHASE\_47\_FOO.md normalises
        # to PHASE/_47/_FOO.md and is reported missing. Found on first run
        # against the real repo.
        text = text.replace("\\_", "_")
        for match in PATH_RE.findall(text):
            norm = match.replace("\\", "/")
            # Skip globs and placeholders -- they are illustrative, not citations.
            if any(ch in norm for ch in "*?<>"):
                continue
            refs.setdefault(norm, set()).add(name)
    return {k: sorted(v) for k, v in refs.items()}


def check_dangling(known):
    refs = find_references()
    missing_new, missing_known = [], []
    for path in sorted(refs):
        if os.path.exists(os.path.join(REPO_ROOT, path)):
            continue
        if path in known:
            missing_known.append((path, known[path], refs[path]))
        else:
            missing_new.append((path, refs[path]))
    return refs, missing_new, missing_known


# Phases 44-46 number versions of the AGREEMENT: the boundary agreement file
# is itself v0.1 (v0.2 for phase 44), and amendments continue that series, so
# the low numbers have no amendment file and never did. Phase 48 instead locks
# its agreement at v1.0 and runs amendments as a separate v0.1.. series.
# Assuming Phase 48's convention produced four false positives on the first
# real run, so the baseline is read out of the amendments themselves.
BASELINE_RE = re.compile(
    r"locked\s+v0\.(\d+)[^)]{0,80}?PHASE_\d+_BOUNDARY_AGREEMENT",
    re.DOTALL | re.IGNORECASE,
)


def check_amendment_gaps():
    families, baselines = {}, {}
    for name in sorted(os.listdir(DOCS_DIR)):
        m = AMENDMENT_RE.match(name)
        if not m:
            continue
        phase, ver = int(m.group(1)), int(m.group(2))
        families.setdefault(phase, set()).add(ver)
        with open(os.path.join(DOCS_DIR, name), "r",
                  encoding="utf-8", errors="replace") as fh:
            head = fh.read(800)
        b = BASELINE_RE.search(head)
        if b:
            baselines[phase] = max(baselines.get(phase, 0), int(b.group(1)))

    gaps = []
    for phase in sorted(families):
        present = families[phase]
        start = baselines.get(phase, 0) + 1
        for v in range(start, max(present) + 1):
            if v not in present:
                gaps.append((phase, v))
    return families, baselines, gaps


def main():
    if not os.path.isdir(DOCS_DIR):
        print("BLOCKED: docs/ not found at " + DOCS_DIR)
        return 2

    known = load_allowlist()
    refs, missing_new, missing_known = check_dangling(known)
    families, baselines, gaps = check_amendment_gaps()

    print("=" * 64)
    print("APEX ULTRA - RECORD INTEGRITY CHECK   [read-only]")
    print("=" * 64)
    print("repo          : " + REPO_ROOT)
    print("docs scanned  : %d" % len([n for n in os.listdir(DOCS_DIR)
                                      if n.endswith(".md")]))
    print("paths cited   : %d" % len(refs))
    print("allowlisted   : %d" % len(known))
    print()

    print("[1] DANGLING REFERENCES")
    if missing_new:
        for path, citers in missing_new:
            print("    MISSING  " + path)
            print("             cited by: " + ", ".join(citers))
    else:
        print("    none")
    if missing_known:
        print()
        print("    known-absent, recorded (not failures):")
        for path, reason, citers in missing_known:
            print("      - " + path)
            print("        " + reason)
    print()

    print("[2] AMENDMENT SEQUENCE")
    if gaps:
        for phase, v in gaps:
            print("    GAP      PHASE_%d_AMENDMENT_V0_%d.md absent" % (phase, v))
    else:
        for phase in sorted(families):
            present = sorted(families[phase])
            base = baselines.get(phase)
            note = ""
            if base:
                note = " (agreement is v0.%d; amendments run from v0.%d)" % (
                    base, base + 1)
            print("    phase %d : v0.%d-v0.%d complete, %d amendments%s"
                  % (phase, present[0], present[-1], len(present), note))
    print()

    findings = len(missing_new) + len(gaps)
    print("=" * 64)
    if findings:
        print("FINDINGS: %d" % findings)
        print("A cited path that does not exist, or a gap in an amendment")
        print("chain, means the record claims something the filesystem does")
        print("not support. Resolve it or add it to tools/known_absent.txt")
        print("with a reason.")
    else:
        print("RECORD INTEGRITY: PASS")
    print("=" * 64)
    print()
    print("NOTE: this cannot see the Claude project mirror. A document written")
    print("there and never cited from docs/ is invisible to this check.")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
