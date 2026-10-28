# Renders the r2 look test (apply_lookdev.py --look r2) for the given buildings, at most 3 at once.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File run_r2.ps1 [-Only id1,id2] [-Samples 128]
param([string[]]$Only = @('hilltop_keep', 'tower_windmill', 'wattle_roundhut', 'v3_longhouse_roundend', 'v4_mixed'),
      [int]$Samples = 128, [int]$MaxParallel = 3)
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$py = Join-Path (Split-Path -Parent $root) '.bpyenv\Scripts\python.exe'
$script = Join-Path $PSScriptRoot 'apply_lookdev.py'
$src = Join-Path $root 'lookdev\r2_src'
$out = Join-Path $root 'lookdev\renders_r2'
New-Item -ItemType Directory -Force $out | Out-Null
$running = @()
foreach ($id in $Only) {
    while (($running | Where-Object { -not $_.HasExited }).Count -ge $MaxParallel) { Start-Sleep -Seconds 5 }
    $rdir = Join-Path $out $id
    New-Item -ItemType Directory -Force $rdir | Out-Null
    $a = @('-I', $script, (Join-Path $src "$id.blend"), $src, '--look', 'r2', '--samples', "$Samples",
           '--render-dir', $rdir, '--blend-out', (Join-Path $src "${id}_lookdev.blend"))
    $p = Start-Process -FilePath $py -ArgumentList $a -RedirectStandardOutput (Join-Path $rdir 'lookdev.log') `
        -RedirectStandardError (Join-Path $rdir 'lookdev.err') -PassThru -NoNewWindow
    "$(Get-Date -Format HH:mm:ss) START $id pid $($p.Id)"
    $running += $p
}
foreach ($p in $running) { $p.WaitForExit() }
"$(Get-Date -Format HH:mm:ss) DONE"
