# Sequential (one bpy process at a time): apply_lookdev r2 -> village_shots for each building.
param([string[]]$Ids = @("hilltop_keep","wattle_roundhut","tower_windmill","v1_stone_watchtower","v2_tiered_hall",
                         "v3_longhouse_roundend","v4_mixed","v5_harbour_house","v6_barn"),
      [switch]$ShotsOnly, [string]$Only = "hero,eye")
$py = "C:\GitHubDesktop\git_test\.bpyenv\Scripts\python.exe"
$root = "C:\GitHubDesktop\git_test\blender_village\lookdev"
$w = "$root\village_r2"
foreach ($id in $Ids) {
    $t0 = Get-Date
    if (-not $ShotsOnly) {
        & $py -I "$root\scripts\apply_lookdev.py" "$w\work\${id}_src.blend" "$w\work" --name $id --look r2 --shots none --blend-out "$w\work\${id}_lookdev.blend" *> "$w\logs\${id}_apply.log"
    }
    & $py -I "$w\scripts\village_shots.py" "$w\work\${id}_lookdev.blend" "$w\renders\$id" --id $id --samples 96 --only $Only *> "$w\logs\${id}_shots.log"
    "{0} done in {1:n0} s" -f $id, ((Get-Date) - $t0).TotalSeconds | Out-File -Append -Encoding utf8 "$w\logs\progress.log"
}
"ALL DONE" | Out-File -Append -Encoding utf8 "$w\logs\progress.log"
