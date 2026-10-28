param([string]$Step = "2_guardrails", [string]$Out = "", [string]$EntFrom = "")
# Runs the UV measurements on the seven kit buildings of kit/baseline/<Step>/:
#   lookdev/scripts/analyze_uv_grain.py (original, unchanged)  -> <Out>/<id>.grain.txt
#   tools/uv_audit.py (adapted copy, every object)              -> <Out>/<id>.json + <id>.audit.txt
# -EntFrom <dir>: take each building's entrance zones from <dir>/<id>.json (an audit of a kit 1.10 build), so a
# pre-fix build with identical geometry is measured on the same door zones.
$root = "C:\GitHubDesktop\git_test\blender_village"
$py = "C:\GitHubDesktop\git_test\.bpyenv\Scripts\python.exe"
if (-not $Out) { $Out = Join-Path $root "kit\baseline\$Step\uv_audit" }
New-Item -ItemType Directory -Force $Out | Out-Null
foreach ($id in "hilltop_keep","wattle_roundhut","tower_windmill","v1_stone_watchtower","v2_tiered_hall","v3_longhouse_roundend","v4_mixed") {
  $blend = Join-Path $root "kit\baseline\$Step\$id\$id.blend"
  if (-not (Test-Path $blend)) { "$id : no blend"; continue }
  $a = @((Join-Path $root "tools\uv_audit.py"), $blend, (Join-Path $Out "$id.json"))
  if ($EntFrom) { $a += @("--entrances", (Join-Path $EntFrom "$id.json")) }
  & $py @a 2>$null | Where-Object { $_ -notmatch "Read blend" } | Out-File -Encoding utf8 (Join-Path $Out "$id.audit.txt")
  & $py (Join-Path $root "lookdev\scripts\analyze_uv_grain.py") $blend 2>$null | Where-Object { $_ -match "^(M_|MASK)" } |
    Out-File -Encoding utf8 (Join-Path $Out "$id.grain.txt")
  "$id done"
}
