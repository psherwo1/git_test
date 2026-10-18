# Labelled contact sheet of the vignette shots (System.Drawing, no bpy).
param([string]$Out = "vignette_sheet.jpg")
Add-Type -AssemblyName System.Drawing
$r = "C:\GitHubDesktop\git_test\blender_village\lookdev\vignette\renders"
$m = @{}
if (Test-Path "$r\measurements.jsonl") {
    Get-Content "$r\measurements.jsonl" | ForEach-Object { $j = $_ | ConvertFrom-Json; $m[$j.shot] = $j }
}
$shots = @(
    @("s1_A", "s1 establishing aerial - A r2 day"), @("s1_B", "s1 establishing aerial - B cinematic + fog"),
    @("s2_A", "s2 street eye level 1.7 m - A r2 day"), @("s2_B", "s2 street eye level 1.7 m - B cinematic + fog"),
    @("s3_A", "s3 harbour, water level - A r2 day"), @("s4_A", "s4 50 mm detail (mill-house, hall, barn) - A"))
$cols = 2; $tw = 960; $th = 540; $lab = 40; $pad = 12; $head = 56
$rows = [math]::Ceiling($shots.Count / $cols)
$SW = $cols * $tw + ($cols + 1) * $pad
$SH = $head + $rows * ($th + $lab) + ($rows + 1) * $pad
$bmp = New-Object System.Drawing.Bitmap $SW, $SH
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$g.Clear([System.Drawing.Color]::FromArgb(24, 24, 24))
$f = New-Object System.Drawing.Font "Segoe UI", 19, ([System.Drawing.FontStyle]::Bold), ([System.Drawing.GraphicsUnit]::Pixel)
$fh = New-Object System.Drawing.Font "Segoe UI", 25, ([System.Drawing.FontStyle]::Bold), ([System.Drawing.GraphicsUnit]::Pixel)
$br = [System.Drawing.Brushes]::WhiteSmoke
$g.DrawString("Village vignette - nine r2 buildings, fjord harbour layout (Cycles OptiX 1920x1080, denoised)", $fh, $br, $pad, 14)
$sf = New-Object System.Drawing.StringFormat
$sf.Alignment = [System.Drawing.StringAlignment]::Center
for ($i = 0; $i -lt $shots.Count; $i++) {
    $c = $i % $cols; $rw = [math]::Floor($i / $cols)
    $x = $pad + $c * ($tw + $pad); $y = $head + $pad + $rw * ($th + $lab + $pad)
    $p = "$r\$($shots[$i][0]).png"
    if (Test-Path $p) {
        $im = [System.Drawing.Image]::FromFile($p)
        $g.DrawImage($im, $x, $y, $tw, $th)
        $im.Dispose()
    } else {
        $g.DrawString("missing", $f, [System.Drawing.Brushes]::Red, $x + 20, $y + 20)
    }
    $t = $shots[$i][1]
    $j = $m[$shots[$i][0]]
    if ($j) { $t += "   ({0} spp, {1:n0} s)" -f $j.samples, $j.seconds }
    $rect = New-Object System.Drawing.RectangleF $x, ($y + $th + 6), $tw, ($lab - 6)
    $g.DrawString($t, $f, $br, $rect, $sf)
}
$enc = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | ? { $_.MimeType -eq "image/jpeg" }
$ep = New-Object System.Drawing.Imaging.EncoderParameters 1
$ep.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter ([System.Drawing.Imaging.Encoder]::Quality), 90L
$bmp.Save("$r\$Out", $enc, $ep)
$g.Dispose(); $bmp.Dispose()
"saved $r\$Out"
