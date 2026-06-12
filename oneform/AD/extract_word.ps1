try {
    $word = New-Object -ComObject Word.Application
    $doc = $word.Documents.Open('D:\oneform\AD\Search Ads.docx')
    $text = $doc.Content.Text
    $text | Out-File -FilePath 'D:\oneform\AD\tutorial_text.txt' -Encoding UTF8
    $doc.Close()
    $word.Quit()
    Write-Host "Successfully extracted text."
} catch {
    Write-Error $_.Exception.Message
}
