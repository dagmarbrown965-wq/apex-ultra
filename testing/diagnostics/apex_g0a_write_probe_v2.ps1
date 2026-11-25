# apex_g0a_write_probe.ps1
# ---------------------------------------------------------------------------
# PHASE 50 ROUTE 4 - G0a Windows write-capability probe.  v2.
#
# Establishes, for whatever token it is launched under, which durable
# locations that token can READ and WRITE, and whether it can still perform an
# outbound HTTPS request.
#
# SAFETY:
#   - Creates only uniquely named files called _apexprobe_<hex>.* and removes
#     each one immediately, BY EXPLICIT PATH. No wildcard delete anywhere -
#     see deferred-fixes incident I1.
#   - v2 adds the InDir vector (write inside a directory we just created, to
#     catch CREATOR OWNER escalation) and two locations that grant Users
#     create-folder by default: Users\Public and ProgramData. The nested file
#     is removed before its parent directory, both by explicit path, so the
#     -Recurse flag is no longer needed and has been dropped.
#   - Touches no project data, no Deriv endpoint, no credentials.
#   - Changes no ACL and no system setting.
#   - The HTTPS leg contacts example.com only.
# ---------------------------------------------------------------------------
param(
    [string]$Label = 'unlabelled',
    [string]$Repo  = 'C:\Users\dagma\APEX_ULTRA\apex_ultra'
)

$ErrorActionPreference = 'SilentlyContinue'

$targets = @(
    @{ Name = 'repo root';     Path = $Repo },
    @{ Name = 'docs';          Path = (Join-Path $Repo 'docs') },
    @{ Name = 'engine\output'; Path = (Join-Path $Repo 'engine\output') },
    @{ Name = 'USER TEMP';     Path = $env:TEMP },
    @{ Name = 'LOCALAPPDATA';  Path = $env:LOCALAPPDATA },
    @{ Name = 'profile root';  Path = $env:USERPROFILE },
    @{ Name = 'Windows\Temp';  Path = 'C:\Windows\Temp' },
    @{ Name = 'C:\ (root)';    Path = 'C:\' },
    @{ Name = 'Users\Public';  Path = $env:PUBLIC },
    @{ Name = 'ProgramData';   Path = $env:ProgramData }
)

'=== APEX G0a write-capability probe  [' + $Label + '] ==='
'user       : ' + $env:USERNAME
'when       : ' + (Get-Date -Format s)
'repo arg   : ' + $Repo
''
'{0,-15} {1,-8} {2}' -f 'LOCATION', 'READ', 'WRITE VECTORS'
'-' * 92

foreach ($t in $targets) {

    if (-not $t.Path) { '{0,-15} {1}' -f $t.Name, 'PATH EMPTY'; continue }

    # ---- read leg -------------------------------------------------------
    $seen = $null
    $seen = Get-ChildItem -Path $t.Path -Force -ErrorAction SilentlyContinue |
            Select-Object -First 1
    if ($seen) { $read = 'ok' }
    elseif (Test-Path $t.Path) { $read = 'ok/empty' }
    else { $read = 'DENIED' }

    if ($read -eq 'DENIED') {
        '{0,-15} {1,-8} {2}' -f $t.Name, $read, '(not probed - unreadable)'
        continue
    }

    # ---- write leg: five independent vectors ----------------------------
    $stem = Join-Path $t.Path ('_apexprobe_' + [guid]::NewGuid().ToString('N').Substring(0,8))
    $res  = @()

    $p = $stem + '.a'
    Set-Content -Path $p -Value 'x' -ErrorAction SilentlyContinue
    if (Test-Path $p) { $res += 'SetContent:WROTE'; Remove-Item -LiteralPath $p -Force -ErrorAction SilentlyContinue }
    else { $res += 'SetContent:denied' }

    $p = $stem + '.b'
    try { [System.IO.File]::WriteAllText($p, 'x') } catch { }
    if (Test-Path $p) { $res += 'NetWrite:WROTE'; Remove-Item -LiteralPath $p -Force -ErrorAction SilentlyContinue }
    else { $res += 'NetWrite:denied' }

    $p = $stem + '.c'
    New-Item -Path $p -ItemType File -ErrorAction SilentlyContinue | Out-Null
    if (Test-Path $p) { $res += 'NewItem:WROTE'; Remove-Item -LiteralPath $p -Force -ErrorAction SilentlyContinue }
    else { $res += 'NewItem:denied' }

    $p = $stem + '.d'
    try { 'x' | Out-File -FilePath $p -ErrorAction SilentlyContinue } catch { }
    if (Test-Path $p) { $res += 'OutFile:WROTE'; Remove-Item -LiteralPath $p -Force -ErrorAction SilentlyContinue }
    else { $res += 'OutFile:denied' }

    # vector 5: directory creation, AND the escalation it enables.
    # A directory you create you own, so CREATOR OWNER may grant full control
    # inside it even where the parent denies file creation. A boundary that
    # stops files but allows folders is not a boundary.
    $p = $stem + '.dir'
    New-Item -Path $p -ItemType Directory -ErrorAction SilentlyContinue | Out-Null
    if (Test-Path $p) {
        $res += 'MkDir:WROTE'
        $inner = Join-Path $p 'inner.txt'
        Set-Content -Path $inner -Value 'x' -ErrorAction SilentlyContinue
        if (Test-Path $inner) {
            $res += 'InDir:WROTE'
            Remove-Item -LiteralPath $inner -Force -ErrorAction SilentlyContinue
        } else { $res += 'InDir:denied' }
        Remove-Item -LiteralPath $p -Force -ErrorAction SilentlyContinue
    }
    else { $res += 'MkDir:denied'; $res += 'InDir:n/a' }

    '{0,-15} {1,-8} {2}' -f $t.Name, $read, ($res -join '  ')
}

''
'--- network leg: can this token still fetch? ---'
try {
    $r = Invoke-WebRequest -Uri 'https://example.com' -UseBasicParsing -TimeoutSec 20
    'HTTPS GET  : OK   status ' + $r.StatusCode
} catch {
    'HTTPS GET  : FAILED   ' + $_.Exception.Message
}

''
'--- leftover check: nothing of ours should remain ---'
foreach ($t in $targets) {
    if (-not $t.Path -or -not (Test-Path $t.Path)) { continue }
    $left = Get-ChildItem -Path $t.Path -Filter '_apexprobe_*' -Force -ErrorAction SilentlyContinue
    if ($left) { 'LEFTOVER in ' + $t.Name + ' : ' + ($left.Name -join ', ') }
}
'=== end [' + $Label + '] ==='
