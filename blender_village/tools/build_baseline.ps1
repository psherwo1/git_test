param([string]$Step = "0_baseline", [int]$MaxParallel = 3, [string[]]$Only = @())
# Builds the seven kit buildings into kit/baseline/<Step>/<id>/<id>.blend (max $MaxParallel at once),
# then fingerprints each one into kit/baseline/<Step>/<id>.json.  Times are wall-clock per build.
$ErrorActionPreference = "Stop"
$root = "C:\GitHubDesktop\git_test\blender_village"
$py = "C:\GitHubDesktop\git_test\.bpyenv\Scripts\python.exe"
$base = Join-Path $root "kit\baseline\$Step"
New-Item -ItemType Directory -Force $base | Out-Null
$jobs = @(
  @{id="hilltop_keep"; script="buildings\hilltop_keep\build_hilltop_keep.py"; env="KEEP_OUT"},
  @{id="wattle_roundhut"; script="buildings\wattle_roundhut\build_wattle_roundhut.py"; env="HUT_OUT"},
  @{id="tower_windmill"; script="buildings\tower_windmill\build_tower_windmill.py"; env="MILL_OUT"},
  @{id="v1_stone_watchtower"; script="buildings\variants\v1_stone_watchtower\build_v1_stone_watchtower.py"; env="WATCH_OUT"},
  @{id="v2_tiered_hall"; script="buildings\variants\v2_tiered_hall\build_v2_tiered_hall.py"; env="HALL_OUT"},
  @{id="v3_longhouse_roundend"; script="buildings\variants\v3_longhouse_roundend\build_v3_longhouse_roundend.py"; env="LONG_OUT"},
  @{id="v4_mixed"; script="buildings\variants\v4_mixed\build_v4_mixed.py"; env="V4_OUT"},
  @{id="v5_harbour_house"; script="buildings\variants\v5_harbour_house\build_v5_harbour_house.py"; env="HARB_OUT"}
)
if ($Only.Count -gt 0) { $jobs = $jobs | Where-Object { $Only -contains $_.id } }
$queue = New-Object System.Collections.Queue
$jobs | ForEach-Object { $queue.Enqueue($_) }
$running = @()
$results = @{}
function Start-Build($j) {
  $dir = Join-Path $base $j.id
  New-Item -ItemType Directory -Force $dir | Out-Null
  $out = Join-Path $dir ($j.id + ".blend")
  Set-Item -Path ("env:" + $j.env) -Value $out
  $p = Start-Process -FilePath $py -ArgumentList @((Join-Path $root $j.script)) -WorkingDirectory $dir `
        -RedirectStandardOutput (Join-Path $dir "build.log") -RedirectStandardError (Join-Path $dir "build.err") `
        -NoNewWindow -PassThru
  $null = $p.Handle   # cache the handle so ExitCode is available after exit (Windows PowerShell 5.1)
  Remove-Item -Path ("env:" + $j.env)
  "$(Get-Date -Format HH:mm:ss) START $($j.id) pid $($p.Id)" | Tee-Object -Append (Join-Path $base "runner.log")
  return @{job=$j; proc=$p; t0=Get-Date; out=$out}
}
while ($queue.Count -gt 0 -or $running.Count -gt 0) {
  while ($queue.Count -gt 0 -and $running.Count -lt $MaxParallel) { $running += ,(Start-Build $queue.Dequeue()) }
  Start-Sleep -Seconds 5
  $still = @()
  foreach ($r in $running) {
    if ($r.proc.HasExited) {
      $secs = [int]((Get-Date) - $r.t0).TotalSeconds
      $code = $r.proc.ExitCode
      "$(Get-Date -Format HH:mm:ss) END $($r.job.id) exit $code in $secs s" | Tee-Object -Append (Join-Path $base "runner.log")
      $results[$r.job.id] = @{secs=$secs; code=$code; out=$r.out}
    } else { $still += ,$r }
  }
  $running = $still
}
# fingerprints (sequential, after the builds)
foreach ($j in $jobs) {
  $r = $results[$j.id]
  $json = Join-Path $base ($j.id + ".json")
  if (Test-Path $r.out) {
    $h = & $py (Join-Path $root "tools\geom_hash.py") $r.out $json | Select-String "GEOM_HASH"
    "$($j.id) build_s=$($r.secs) exit=$($r.code) $h" | Tee-Object -Append (Join-Path $base "runner.log")
  } else {
    "$($j.id) build_s=$($r.secs) exit=$($r.code) NO BLEND" | Tee-Object -Append (Join-Path $base "runner.log")
  }
}
$results.GetEnumerator() | ForEach-Object { [pscustomobject]@{id=$_.Key; secs=$_.Value.secs; code=$_.Value.code} } |
  ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $base "build_times.json")
"DONE" | Tee-Object -Append (Join-Path $base "runner.log")

