# Labelled contact sheets of the village r2 shots (System.Drawing, no bpy).
param([string]$Shot = "hero", [string]$Out = "village_contact_sheet.jpg", [string]$Title = "")
Add-Type -AssemblyName System.Drawing
$w = "C:\GitHubDesktop\git_test\blender_village\lookdev\village_r2"
$ids = @("hilltop_keep","wattle_roundhut","tower_windmill","v1_stone_watchtower","v2_tiered_hall",
         "v3_longhouse_roundend","v4_mixed","v5_harbour_house","v6_barn")
$cols = 3; $tw = 960; $th = 540; $lab = 44; $pad = 12; $head = 60
$rows = [math]::Ceiling($ids.Count / $cols)
$SW = $cols * $tw + ($cols + 1) * $pad
$SH = $head + $rows * ($th + $lab) + ($rows + 1) * $pad
$bmp = New-Object System.Drawing.Bitmap $SW, $SH
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$g.Clear([System.Drawing.Color]::FromArgb(24, 24, 24))
$f = New-Object System.Drawing.Font "Segoe UI", 20, ([System.Drawing.FontStyle]::Bold), ([System.Drawing.GraphicsUnit]::Pixel)
$fh = New-Object System.Drawing.Font "Segoe UI", 26, ([System.Drawing.FontStyle]::Bold), ([System.Drawing.GraphicsUnit]::Pixel)
$br = [System.Drawing.Brushes]::WhiteSmoke
$g.DrawString($Title, $fh, $br, $pad, 14)
$sf = New-Object System.Drawing.StringFormat
$sf.Alignment = [System.Drawing.StringAlignment]::Center
for ($i = 0; $i -lt $ids.Count; $i++) {
    $c = $i % $cols; $r = [math]::Floor($i / $cols)
    $x = $pad + $c * ($tw + $pad); $y = $head + $pad + $r * ($th + $lab + $pad)
    $p = "$w\renders\$($ids[$i])\$Shot.png"
    if (Test-Path $p) {
        $im = [System.Drawing.Image]::FromFile($p)
        $g.DrawImage($im, $x, $y, $tw, $th)
        $im.Dispose()
    } else {
        $g.DrawString("missing", $f, [System.Drawing.Brushes]::Red, $x + 20, $y + 20)
    }
    $rect = New-Object System.Drawing.RectangleF $x, ($y + $th + 6), $tw, ($lab - 6)
    $g.DrawString($ids[$i], $f, $br, $rect, $sf)
}
$enc = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | ? { $_.MimeType -eq "image/jpeg" }
$ep = New-Object System.Drawing.Imaging.EncoderParameters 1
$ep.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter ([System.Drawing.Imaging.Encoder]::Quality), 90L
New-Item -ItemType Directory -Force "$w\renders\sheet" | Out-Null
$bmp.Save("$w\renders\sheet\$Out", $enc, $ep)
$g.Dispose(); $bmp.Dispose()
"saved $w\renders\sheet\$Out"

