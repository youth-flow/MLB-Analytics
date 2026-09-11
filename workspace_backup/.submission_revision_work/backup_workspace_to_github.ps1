$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent $PSScriptRoot
$repo = Join-Path $workspace 'MLB-Analytics'
$destination = Join-Path $repo 'workspace_backup'
if (Test-Path -LiteralPath $destination) { throw 'Backup destination already exists; inspect before replacing.' }
$files = [System.Collections.Generic.List[System.IO.FileInfo]]::new()
foreach ($item in Get-ChildItem -LiteralPath $workspace -File -Force) { $files.Add($item) }
foreach ($item in Get-ChildItem -LiteralPath (Join-Path $workspace '提交材料') -Recurse -File -Force) { $files.Add($item) }
$excluded = [System.Collections.Generic.List[object]]::new()
$revision = Join-Path $workspace '.submission_revision_work'
foreach ($item in Get-ChildItem -LiteralPath $revision -Recurse -File -Force) {
    $relative = [System.IO.Path]::GetRelativePath($workspace, $item.FullName).Replace('\', '/')
    $reason = $null
    if ($relative -match '/__pycache__/|\.py[co]$') { $reason = 'Regenerable Python bytecode cache' }
    elseif ($relative -match '^\.submission_revision_work/render_tools/(download/|libreoffice-local/)') { $reason = 'Reinstallable LibreOffice installer and third-party runtime' }
    elseif ($relative -eq '.submission_revision_work/render_tools/libreoffice-extract.log') { $reason = 'LibreOffice installer extraction log' }
    if ($reason) { $excluded.Add([pscustomobject]@{path=$relative; bytes=$item.Length; reason=$reason}); continue }
    if ($item.Name -like '~$*') { $excluded.Add([pscustomobject]@{path=$relative; bytes=$item.Length; reason='Temporary Office lock'}); continue }
    $files.Add($item)
}
$records = [System.Collections.Generic.List[object]]::new()
foreach ($item in ($files | Sort-Object FullName)) {
    $relative = [System.IO.Path]::GetRelativePath($workspace, $item.FullName)
    $target = [System.IO.Path]::GetFullPath((Join-Path $destination $relative))
    if (-not $target.StartsWith($destination + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Destination escaped backup directory' }
    if ($item.Length -ge 100MB) { throw "File exceeds GitHub regular Git limit: $relative" }
    New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
    Copy-Item -LiteralPath $item.FullName -Destination $target
    $before = (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash
    $after = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
    if ($before -ne $after) { throw "Copy hash mismatch: $relative" }
    $records.Add([pscustomobject]@{path=$relative.Replace('\','/'); bytes=$item.Length; sha256=$after})
}
$inventory = [ordered]@{
    schema_version=1
    created_utc=[DateTime]::UtcNow.ToString('o')
    scope='All coursework workspace files except the separately tracked MLB-Analytics repository, third-party render runtime, installer log and regenerable caches'
    file_count=$records.Count
    total_bytes=($records | Measure-Object bytes -Sum).Sum
    files=$records.ToArray()
    exclusions=$excluded.ToArray()
}
$inventory | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $destination 'BACKUP_MANIFEST.json') -Encoding utf8NoBOM
Write-Output "COPIED_AND_SHA256_VERIFIED=$($records.Count)"
Write-Output "TOTAL_BYTES=$($inventory.total_bytes)"
Write-Output "EXCLUDED_RUNTIME_AND_CACHE_FILES=$($excluded.Count)"
