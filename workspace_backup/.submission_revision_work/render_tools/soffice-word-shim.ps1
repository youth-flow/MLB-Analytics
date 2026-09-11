param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $SofficeArgs
)

$ErrorActionPreference = 'Stop'
$format = $null
$outDir = $null
$inputPath = $null

for ($index = 0; $index -lt $SofficeArgs.Count; $index++) {
    if ($SofficeArgs[$index] -eq '--convert-to' -and $index + 1 -lt $SofficeArgs.Count) {
        $format = $SofficeArgs[$index + 1]
        $index++
        continue
    }
    if ($SofficeArgs[$index] -eq '--outdir' -and $index + 1 -lt $SofficeArgs.Count) {
        $outDir = $SofficeArgs[$index + 1]
        $index++
        continue
    }
    if (Test-Path -LiteralPath $SofficeArgs[$index] -PathType Leaf) {
        $inputPath = (Resolve-Path -LiteralPath $SofficeArgs[$index]).Path
    }
}

if ($format -ne 'pdf') {
    throw "The local Word rendering shim supports PDF output only; requested: $format"
}
if (-not $outDir -or -not $inputPath) {
    throw 'Missing --outdir or input document.'
}

$resolvedOutDir = [System.IO.Path]::GetFullPath($outDir)
[System.IO.Directory]::CreateDirectory($resolvedOutDir) | Out-Null
$pdfPath = Join-Path $resolvedOutDir (([System.IO.Path]::GetFileNameWithoutExtension($inputPath)) + '.pdf')

$word = $null
$document = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open($inputPath, $false, $true, $false)
    $document.ExportAsFixedFormat($pdfPath, 17)
}
finally {
    if ($null -ne $document) {
        $document.Close(0)
        [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($document)
    }
    if ($null -ne $word) {
        $word.Quit(0)
        [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($word)
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

Write-Output "convert $inputPath -> $pdfPath using Microsoft Word"

