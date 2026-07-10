import argparse, sys
from urllib.parse import parse_qs

def redact(t):
    if not t: return "<empty>"
    if len(t) <= 12: return "len=" + str(len(t)) + " <short,hidden>"
    return "len=" + str(len(t)) + " prefix=" + t[:6] + " suffix=" + t[-4:]

def extract_accounts(s):
    raw = s.strip()
    for sep in ("?", "#"):
        if sep in raw: raw = raw.split(sep, 1)[1]
    qs = parse_qs(raw, keep_blank_values=True)
    accts = {}
    for k, v in qs.items():
        val = v[0] if v else ""
        for f in ("acct", "token", "cur"):
            if k.startswith(f) and k[len(f):].isdigit():
                i = int(k[len(f):])
                accts.setdefault(i, {"index": i})[f] = val
    out = [a for a in accts.values() if a.get("token")]
    out.sort(key=lambda a: a["index"])
    return out

def is_virtual(a): return a.upper().startswith("VRT")
def is_legacy(t): return t.startswith("a1-") or (t.startswith("a1") and not t.startswith("a1_"))

def report(accts):
    if not accts:
        print("    (no acctN/tokenN pairs found)")
        return
    for a in accts:
        kind = "DEMO" if is_virtual(a.get("acct", "")) else "real"
        t = a.get("token", "")
        k = "a1-legacy" if is_legacy(t) else ("ory-new" if t.startswith("ory") else "unknown")
        line = "    [" + str(a["index"]) + "] " + kind + " acct=" + a.get("acct", "?") + " kind=" + k + " " + redact(t)
        print(line)

def pick_demo(accts):
    d = [a for a in accts if is_virtual(a.get("acct", ""))]
    return d[0] if d else None

def finalize(token, acct, out):
    if not token:
        print("\nNo token selected.")
        return 1
    ok = is_legacy(token)
    q = chr(39)
    print("\n" + "=" * 60)
    print("SELECTED DEMO TOKEN")
    print("=" * 60)
    print("    account    : " + acct)
    print("    token      : " + redact(token))
    print("    token kind : " + ("a1- legacy (compatible)" if ok else "NON-a1- (likely will NOT pass legacy authorize)"))
    try:
        fh = open(out, "w", encoding="utf-8")
        fh.write("DERIV_API_TOKEN=" + token + "\n")
        fh.close()
        print("\n    full token written to: " + out + "  (keep private; delete after use)")
    except OSError as e:
        print("\n    WARNING could not write " + out + ": " + str(e))
    print("\nNEXT (PowerShell):")
    print("    $env:DERIV_API_TOKEN = (Get-Content " + out + ").Split(" + q + "=" + q + ",2)[1]")
    print("    $env:DERIV_APP_ID=" + q + "1089" + q)
    print("    $env:LIVE_TRADING=" + q + "false" + q)
    print("    py -m testing.diagnostics.deriv_auth_probe")
    print("\nExpected on success: RESULT: OK_DEMO")
    return 0

def main():
    print("=" * 60)
    print("DERIV OAUTH CAPTURE - PASTE MODE")
    print("=" * 60)
    print("Paste the FULL redirect URL containing acct1=...token1=a1-... then Enter.\n")
    try:
        pasted = input("redirect URL > ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return 1
    if not pasted:
        print("Nothing pasted.")
        return 1
    accts = extract_accounts(pasted)
    print("\nAccounts found:")
    report(accts)
    d = pick_demo(accts)
    if not d:
        print("\nNo VRTC demo token found in what you pasted.")
        return 1
    return finalize(d["token"], d.get("acct", "?"), "captured_token.env")

sys.exit(main())
