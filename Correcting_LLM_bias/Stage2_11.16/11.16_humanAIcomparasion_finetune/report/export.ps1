param($in, $docx, $pdf)
$w = New-Object -ComObject Word.Application
$w.Visible = $false
$d = $w.Documents.Open($in)
foreach ($t in $d.TablesOfContents) { $t.Update() }
$d.Fields.Update() | Out-Null
$d.SaveAs2($docx, 16)
$d.ExportAsFixedFormat($pdf, 17)
$d.Close($false); $w.Quit()
"done"
