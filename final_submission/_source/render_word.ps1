param([string]$Round='final',[string]$DocumentDir='',[string]$PdftoppmPath='')
$ErrorActionPreference='Stop'
$workspace=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if($DocumentDir){$source=$DocumentDir}
elseif((Split-Path -Leaf $PSScriptRoot) -eq '_source'){$source=Split-Path -Parent $PSScriptRoot}
else{$source=Join-Path $workspace '提交材料\最终提交两份'}
if(-not $PdftoppmPath){
  $converter=Get-Command pdftoppm.exe -ErrorAction SilentlyContinue
  if($converter){$PdftoppmPath=$converter.Source}
  elseif(Test-Path -LiteralPath 'D:\texlive\2025\bin\windows\pdftoppm.exe'){$PdftoppmPath='D:\texlive\2025\bin\windows\pdftoppm.exe'}
  else{throw 'Specify -PdftoppmPath or add pdftoppm.exe to PATH.'}
}
$render=Join-Path $PSScriptRoot ('render_'+$Round)
$word=New-Object -ComObject Word.Application
$word.Visible=$false
$word.DisplayAlerts=0
try {
  foreach($job in @(@{key='report';name='实习报告_杨炎新_15页.docx'},@{key='executive';name='蒋总汇总_今井达也MLB调整建议_2页.docx'})){
    $dir=Join-Path $render $job.key
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
    $pdf=Join-Path $dir ($job.key+'.pdf')
    $doc=$word.Documents.Open((Join-Path $source $job.name),$false,$true,$false)
    try { $doc.Repaginate(); $pages=$doc.ComputeStatistics(2); $doc.ExportAsFixedFormat($pdf,17); Write-Output "$($job.key) PAGES=$pages" }
    finally { $doc.Close(0); [System.Runtime.InteropServices.Marshal]::ReleaseComObject($doc)|Out-Null }
    & $PdftoppmPath -png -r 120 $pdf (Join-Path $dir 'page')
    if($LASTEXITCODE -ne 0){throw 'PDF rasterization failed'}
  }
}
finally { $word.Quit();[System.Runtime.InteropServices.Marshal]::ReleaseComObject($word)|Out-Null;[GC]::Collect() }
