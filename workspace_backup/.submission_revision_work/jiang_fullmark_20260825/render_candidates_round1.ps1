param(
    [string]$Round = 'round1',
    [string]$SourceRelative = '.submission_revision_work\output'
)

$ErrorActionPreference = 'Stop'

$root = 'C:\Users\yyx\Desktop\大三暑期短学期'
$source = Join-Path $root $SourceRelative
$renderRoot = Join-Path $root ('.submission_revision_work\jiang_fullmark_20260825\word_render_' + $Round)
$jobs = @(
    @{ Key = 'exec'; Name = '蒋总汇总_今井达也MLB调整决策_两页版.docx' },
    @{ Key = 'draft01'; Name = '底稿01_今井达也MLB调整决策_完整分析.docx' },
    @{ Key = 'draft02'; Name = '底稿02_MLB数据来源与指标口径.docx' },
    @{ Key = 'draft03'; Name = '底稿03_MLB分析迭代与反证记录.docx' },
    @{ Key = 'draft04'; Name = '底稿04_MLB复现与交付核查说明.docx' }
)

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0

try {
    foreach ($job in $jobs) {
        $docx = Join-Path $source $job.Name
        $out = Join-Path $renderRoot $job.Key
        $pdf = Join-Path $out ($job.Name -replace '\.docx$', '.pdf')
        New-Item -ItemType Directory -Force -Path $out | Out-Null

        $doc = $null
        try {
            $doc = $word.Documents.Open($docx, $false, $true, $false)
            $doc.Repaginate()
            $pages = $doc.ComputeStatistics(2)
            $doc.ExportAsFixedFormat($pdf, 17)
            Write-Output ("WORD_OPEN=PASS|KEY={0}|PAGES={1}|DOCX={2}" -f $job.Key, $pages, $docx)
        }
        finally {
            if ($null -ne $doc) {
                $doc.Close(0)
                [System.Runtime.InteropServices.Marshal]::ReleaseComObject($doc) | Out-Null
            }
        }

        $prefix = Join-Path $out 'page'
        & 'D:\texlive\2025\bin\windows\pdftoppm.exe' -png -r 150 $pdf $prefix
        if ($LASTEXITCODE -ne 0) {
            throw "pdftoppm failed for $pdf"
        }
        $pngs = @(Get-ChildItem -LiteralPath $out -Filter 'page-*.png' | Sort-Object Name)
        Write-Output ("PNG_COUNT={0}|KEY={1}|OUT={2}" -f $pngs.Count, $job.Key, $out)
    }
}
finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
