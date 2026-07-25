[CmdletBinding()]
param(
    [string]$PresentationPath = "presentation\renewable_operations_demo.pptx",
    [string]$PdfPath = "presentation\renewable_operations_demo.pdf",
    [string]$RenderDirectory = "presentation\rendered"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$presentationFile = [System.IO.Path]::GetFullPath((Join-Path $projectRoot $PresentationPath))
$pdfFile = [System.IO.Path]::GetFullPath((Join-Path $projectRoot $PdfPath))
$pdfExportFile = [System.IO.Path]::ChangeExtension($pdfFile, ".exporting.pdf")
$renderFolder = [System.IO.Path]::GetFullPath((Join-Path $projectRoot $RenderDirectory))

if (-not (Test-Path -LiteralPath $presentationFile -PathType Leaf)) {
    throw "Presentation not found: $presentationFile"
}

New-Item -ItemType Directory -Path $renderFolder -Force | Out-Null
$projectRootPrefix = $projectRoot.TrimEnd('\') + '\'
if (-not $renderFolder.StartsWith($projectRootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Render directory must stay inside the project: $renderFolder"
}
if (-not $pdfExportFile.StartsWith($projectRootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Temporary PDF must stay inside the project: $pdfExportFile"
}
if (Test-Path -LiteralPath $pdfExportFile -PathType Leaf) {
    Remove-Item -LiteralPath $pdfExportFile -Force
}
Get-ChildItem -LiteralPath $renderFolder -Filter "*.PNG" -File |
    ForEach-Object { Remove-Item -LiteralPath $_.FullName -Force }

$powerPoint = $null
$presentation = $null
try {
    $powerPoint = New-Object -ComObject PowerPoint.Application
    $presentation = $powerPoint.Presentations.Open($presentationFile, $true, $false, $false)
    # 32 = ppSaveAsPDF. SaveAs is more reliable than ExportAsFixedFormat
    # across Office interop versions installed on Windows.
    $presentation.SaveAs($pdfExportFile, 32)
    $presentation.Export($renderFolder, "PNG", 1920, 1080)
}
finally {
    if ($null -ne $presentation) {
        $presentation.Close()
    }
    if ($null -ne $powerPoint) {
        $powerPoint.Quit()
    }
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}

Copy-Item -LiteralPath $pdfExportFile -Destination $pdfFile -Force
Remove-Item -LiteralPath $pdfExportFile -Force

$renderedSlides = Get-ChildItem -LiteralPath $renderFolder -Filter "*.PNG" -File
[pscustomobject]@{
    Presentation = $presentationFile
    Pdf = $pdfFile
    RenderedSlides = $renderedSlides.Count
} | ConvertTo-Json
