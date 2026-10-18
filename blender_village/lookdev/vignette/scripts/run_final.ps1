# Final vignette renders (one bpy process at a time) with a GPU memory sampler (nvidia-smi, 0.5 s).
param([int]$SamplesA = 128, [int]$SamplesB = 128)
$py = "C:\GitHubDesktop\git_test\.bpyenv\Scripts\python.exe"
$v = "C:\GitHubDesktop\git_test\blender_village\lookdev\vignette"
$blend = "$v\work\vignette.blend"
$r = "$v\renders"
$jl = "$r\measurements.jsonl"
if (Test-Path $jl) { Remove-Item $jl }
$smi = Start-Process -FilePath "nvidia-smi" -ArgumentList "--query-gpu=timestamp,memory.used,memory.total,utilization.gpu --format=csv,noheader -lms 500 -f $v\logs\gpu.csv" -PassThru -WindowStyle Hidden
"start $(Get-Date -Format o)" | Out-File -Encoding utf8 "$v\logs\final_progress.log"
& $py -I "$v\scripts\render_vignette.py" $blend $r --shots s1_A,s2_A,s1_B,s2_B --samples-a $SamplesA --samples-b $SamplesB --noise --log $jl *> "$v\logs\final_ab.log"
"ab done $(Get-Date -Format o)" | Out-File -Append -Encoding utf8 "$v\logs\final_progress.log"
& $py -I "$v\scripts\render_vignette.py" $blend $r --shots s3_A,s4_A --samples-a $SamplesA --log $jl *> "$v\logs\final_s34.log"
"s34 done $(Get-Date -Format o)" | Out-File -Append -Encoding utf8 "$v\logs\final_progress.log"
& $py -I "$v\scripts\render_vignette.py" $blend "$r\b512" --shots s1_B,s2_B --samples-b 512 --log "$r\b512\measurements_b512.jsonl" *> "$v\logs\final_b512.log"
"b512 done $(Get-Date -Format o)" | Out-File -Append -Encoding utf8 "$v\logs\final_progress.log"
Stop-Process -Id $smi.Id -ErrorAction SilentlyContinue
"ALL DONE $(Get-Date -Format o)" | Out-File -Append -Encoding utf8 "$v\logs\final_progress.log"
