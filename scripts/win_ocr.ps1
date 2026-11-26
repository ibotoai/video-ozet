# Windows'un yerlesik OCR'i (Windows.Media.Ocr). powershell.exe (5.1) ile calisir, pwsh 7 ile degil.
# Girdi: her satirda bir gorsel yolu olan liste dosyasi. Cikti: her gorsel icin bir JSON satiri.
param([Parameter(Mandatory)][string]$Liste, [Parameter(Mandatory)][string]$Cikti, [string]$Dil = 'tr')
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTask = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' } | Select-Object -First 1
function Bekle($islem, [Type]$tur) {
    $t = $asTask.MakeGenericMethod($tur).Invoke($null, @($islem)); [void]$t.Wait(-1); $t.Result
}
[void][Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
[void][Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
[void][Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics, ContentType = WindowsRuntime]
[void][Windows.Globalization.Language, Windows.Globalization, ContentType = WindowsRuntime]
$diller = @([Windows.Media.Ocr.OcrEngine]::AvailableRecognizerLanguages)
$secilen = $diller | Where-Object { $_.LanguageTag -eq $Dil } | Select-Object -First 1
if (-not $secilen) { $secilen = $diller | Where-Object { $_.LanguageTag.StartsWith("$Dil-") } | Select-Object -First 1 }
if (-not $secilen) { $secilen = $diller | Where-Object { $_.LanguageTag -eq 'en-US' } | Select-Object -First 1 }
if (-not $secilen) { $secilen = $diller | Select-Object -First 1 }
if (-not $secilen) { throw 'OCR yok: yuklu dil bulunamadi' }
if ($secilen.LanguageTag -ne $Dil) { Write-Warning "OCR dili $Dil yerine $($secilen.LanguageTag) kullaniliyor" }
$motor = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($secilen)
if (-not $motor) { throw 'OCR motoru baslatilamadi' }
$yaz = [System.IO.StreamWriter]::new($Cikti, $false, [System.Text.UTF8Encoding]::new($false))
foreach ($yol in [System.IO.File]::ReadAllLines($Liste, [System.Text.Encoding]::UTF8)) {
    if (-not $yol) { continue }
    $kayit = [ordered]@{ yol = $yol; satirlar = @() }
    try {
        $dosya = Bekle ([Windows.Storage.StorageFile]::GetFileFromPathAsync($yol)) ([Windows.Storage.StorageFile])
        $akis = Bekle ($dosya.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
        $coz = Bekle ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($akis)) ([Windows.Graphics.Imaging.BitmapDecoder])
        $bmp = Bekle ($coz.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
        $sonuc = Bekle ($motor.RecognizeAsync($bmp)) ([Windows.Media.Ocr.OcrResult])
        $kayit.g = $bmp.PixelWidth; $kayit.y = $bmp.PixelHeight
        $kayit.satirlar = @(foreach ($s in $sonuc.Lines) {
            $x1 = 1e9; $y1 = 1e9; $x2 = 0; $y2 = 0
            foreach ($k in $s.Words) {
                $r = $k.BoundingRect
                $x1 = [Math]::Min($x1, $r.X); $y1 = [Math]::Min($y1, $r.Y)
                $x2 = [Math]::Max($x2, $r.X + $r.Width); $y2 = [Math]::Max($y2, $r.Y + $r.Height)
            }
            [ordered]@{ metin = $s.Text; kutu = @([int]$x1, [int]$y1, [int]$x2, [int]$y2) }
        })
        $bmp.Dispose(); $akis.Dispose()
    } catch { $kayit.hata = "$_" }
    $yaz.WriteLine(($kayit | ConvertTo-Json -Compress -Depth 5))
}
$yaz.Close()
