$ErrorActionPreference = 'Stop'

$root = 'C:\Users\yyx\Desktop\大三暑期短学期'
$jobs = @(
    @{
        Docx = Join-Path $root '提交材料\01_每周实习记录\第3周实习记录.docx'
        Pdf = Join-Path $root '.submission_revision_work\delivery_week3_20260825.pdf'
        Out = Join-Path $root '.submission_revision_work\delivery_week3_render_20260825'
    },
    @{
        Docx = Join-Path $root '提交材料\01_每周实习记录\第4周实习记录.docx'
        Pdf = Join-Path $root '.submission_revision_work\delivery_week4_20260825.pdf'
        Out = Join-Path $root '.submission_revision_work\delivery_week4_render_20260825'
    }
)

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0

try {
    foreach ($job in $jobs) {
        New-Item -ItemType Directory -Force -Path $job.Out | Out-Null
        $doc = $null
        try {
            $doc = $word.Documents.Open($job.Docx, $false, $true, $false)
            $pages = $doc.ComputeStatistics(2)
            $doc.ExportAsFixedFormat($job.Pdf, 17)
            Write-Output ("WORD_OPEN=PASS|PAGES={0}|DOCX={1}" -f $pages, $job.Docx)
        }
        finally {
            if ($null -ne $doc) {
                $doc.Close(0)
                [System.Runtime.InteropServices.Marshal]::ReleaseComObject($doc) | Out-Null
            }
        }

        $prefix = Join-Path $job.Out 'page'
        & 'D:\texlive\2025\bin\windows\pdftoppm.exe' -png -r 150 $job.Pdf $prefix
        if ($LASTEXITCODE -ne 0) {
            throw "pdftoppm failed for $($job.Pdf)"
        }
        $pngs = @(Get-ChildItem -LiteralPath $job.Out -Filter 'page-*.png' | Sort-Object Name)
        Write-Output ("PNG_COUNT={0}|OUT={1}" -f $pngs.Count, $job.Out)
    }
}
finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
