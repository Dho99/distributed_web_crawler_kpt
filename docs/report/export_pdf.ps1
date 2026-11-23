param(
    [string]$Docx = (Join-Path $PSScriptRoot "Laporan_Proyek_CrawlMesh_Draft.docx"),
    [string]$Pdf = (Join-Path $PSScriptRoot "Laporan_Proyek_CrawlMesh_Draft.pdf")
)

$ErrorActionPreference = "Stop"
$docxPath = (Resolve-Path $Docx).Path
$pdfPath = [System.IO.Path]::GetFullPath($Pdf)

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0

try {
    $doc = $word.Documents.Open($docxPath, $false, $false)
    $doc.Fields.Update() | Out-Null
    for ($i = 1; $i -le $doc.TablesOfContents.Count; $i++) {
        $doc.TablesOfContents.Item($i).Update()
    }
    $doc.Repaginate()
    $doc.Save()
    $doc.ExportAsFixedFormat($pdfPath, 17)
    $doc.Close($false)

    $repoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
    Copy-Item $docxPath (Join-Path $repoRoot "Laporan_Proyek_CrawlMesh_Draft.docx") -Force
    Copy-Item $pdfPath (Join-Path $repoRoot "Laporan_Proyek_CrawlMesh_Draft.pdf") -Force
    Write-Output "PDF exported: $pdfPath"
    Write-Output "Root copies refreshed."
}
finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
