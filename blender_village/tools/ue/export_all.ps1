# Export every available finished building to export\ue_buildings\<id>\<id>.glb (+ decal_anchors.json, <id>_export.json), ONE Blender process at a time.
# Usage:  powershell -File tools\ue\export_all.ps1 [-Format glb|fbx] [-Only wattle_roundhut,v9_ale_house]
param([string]$Format = "glb", [string[]]$Only = @())
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = (Resolve-Path "$here\..\..").Path                      # blender_village
$py = (Resolve-Path "$root\..\.bpyenv\Scripts\python.exe").Path
$script = "$here\export_building_$Format.py"
$jobs = @()
foreach ($id in "hilltop_keep","wattle_roundhut","tower_windmill","v1_stone_watchtower","v2_tiered_hall","v3_longhouse_roundend","v4_mixed","v5_harbour_house") {
    $jobs += ,@($id, "$root\kit\baseline\1.22.0\$id\$id.blend")           # full-cull baseline builds
}
$jobs += ,@("v7_cottage", "$root\buildings\variants\v7_cottage\v7_cottage.blend")
$jobs += ,@("v8_byre_smokehouse", "$root\buildings\variants\v8_byre_smokehouse\scratch\r2.blend")        # uncut FAST preview
$jobs += ,@("v9_ale_house", "$root\buildings\variants\v9_ale_house\scratch\preview_r2.blend")           # uncut FAST preview
$jobs += ,@("v10_net_loft_cottage", "$root\buildings\variants\v10_net_loft_cottage\scratch\preview_r2.blend")  # uncut FAST preview
foreach ($j in $jobs) {
    $id, $blend = $j
    if ($Only.Count -gt 0 -and $Only -notcontains $id) { continue }
    if (-not (Test-Path $blend)) { Write-Host "skip $id (no $blend)"; continue }
    $out = "$root\export\ue_buildings\$id"
    Write-Host "=== $id ($Format) ==="
    $t = Get-Date
    & $py -I $script $blend $out --id $id
    if ($LASTEXITCODE -ne 0) { Write-Host "FAILED $id (exit $LASTEXITCODE)" } else { Write-Host ("ok {0} in {1:n0} s" -f $id, ((Get-Date) - $t).TotalSeconds) }
}
