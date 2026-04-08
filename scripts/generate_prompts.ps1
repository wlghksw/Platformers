# AI Prompt Data Generator
# AI_prompt_data.txt -> ai_prompt_data.js

$inputFile  = "$PSScriptRoot\..\data\AI_prompt_data.txt"
$outputFile = "$PSScriptRoot\..\assets\js\ai_prompt_data.js"

$categoryMap = @{
    "코딩"        = @{ emoji = "💻"; range = "1-50"   }
    "AI 워크플로우" = @{ emoji = "🤖"; range = "51-100" }
    "리서치"       = @{ emoji = "🔍"; range = "101-150"}
    "자동화"       = @{ emoji = "⚙️"; range = "151-200"}
    "콘텐츠"       = @{ emoji = "✍️"; range = "201-250"}
    "생산성"       = @{ emoji = "📈"; range = "251-300"}
}

function Get-Category($num) {
    if ($num -le 50)  { return "코딩" }
    if ($num -le 100) { return "AI 워크플로우" }
    if ($num -le 150) { return "리서치" }
    if ($num -le 200) { return "자동화" }
    if ($num -le 250) { return "콘텐츠" }
    return "생산성"
}

function Get-Tags($text, $title) {
    $tags = @()
    # 대괄호 속 플레이스홀더 추출 (예: [코드 붙여넣기])
    $matches = [regex]::Matches($text, '\[([^\]]+)\]')
    foreach ($m in $matches) {
        $inner = $m.Groups[1].Value
        if ($inner -notmatch '붙여넣기|설명|숫자|조건|빈도|언어' -and $inner.Length -lt 20) {
            $tags += $inner
        }
    }
    # 제목 키워드 추가
    $titleWords = $title -split ' '
    foreach ($w in $titleWords) {
        if ($w.Length -ge 2) { $tags += $w }
    }
    return ($tags | Select-Object -Unique)
}

function EscapeJs($str) {
    $str = $str -replace '\\', '\\'
    $str = $str -replace '"',  '\"'
    $str = $str -replace "`r`n", '\n'
    $str = $str -replace "`n", '\n'
    $str = $str -replace "`r", '\n'
    return $str
}

$lines = Get-Content $inputFile -Encoding UTF8
$prompts = [System.Collections.Generic.List[hashtable]]::new()

$currentNum   = 0
$currentTitle = ""
$currentLines = [System.Collections.Generic.List[string]]::new()
$collecting   = $false

foreach ($line in $lines) {
    # 섹션 헤더 감지 (# 📋 ... 등) → 무시
    if ($line -match '^# [^\#]') { continue }

    # 프롬프트 헤더 감지: ## #숫자 제목
    if ($line -match '^## #(\d+)\s+(.+)$') {
        # 이전 프롬프트 저장
        if ($currentNum -gt 0 -and $currentLines.Count -gt 0) {
            $text = ($currentLines | Where-Object { $_ -ne '---' } | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }) -join ' '
            $prompts.Add(@{
                id       = $currentNum
                title    = $currentTitle
                prompt   = $text
                category = Get-Category $currentNum
                tags     = Get-Tags $text $currentTitle
            })
        }
        $currentNum   = [int]$Matches[1]
        $currentTitle = $Matches[2].Trim()
        $currentLines = [System.Collections.Generic.List[string]]::new()
        $collecting   = $true
        continue
    }

    # 구분선 제외하고 내용 수집
    if ($collecting -and $line -notmatch '^---$') {
        $currentLines.Add($line)
    }
}

# 마지막 프롬프트 저장
if ($currentNum -gt 0 -and $currentLines.Count -gt 0) {
    $text = ($currentLines | Where-Object { $_ -ne '---' } | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }) -join ' '
    $prompts.Add(@{
        id       = $currentNum
        title    = $currentTitle
        prompt   = $text
        category = Get-Category $currentNum
        tags     = Get-Tags $text $currentTitle
    })
}

# JS 파일 생성
$sb = [System.Text.StringBuilder]::new()
$null = $sb.AppendLine("// AI Prompt Data")
$null = $sb.AppendLine("// Generated from AI_prompt_data.txt")
$null = $sb.AppendLine("// Total: $($prompts.Count) prompts")
$null = $sb.AppendLine("")
$null = $sb.AppendLine("const PROMPTS = [")

for ($i = 0; $i -lt $prompts.Count; $i++) {
    $p    = $prompts[$i]
    $cat  = $p.category
    $info = $categoryMap[$cat]
    $emoji = $info.emoji
    $range = $info.range

    $escapedTitle  = EscapeJs $p.title
    $escapedPrompt = EscapeJs $p.prompt

    $tagsJs = ($p.tags | ForEach-Object { "`"$(EscapeJs $_)`"" }) -join ", "

    $comma = if ($i -lt $prompts.Count - 1) { "," } else { "" }

    $null = $sb.AppendLine("  {")
    $null = $sb.AppendLine("    id: $($p.id),")
    $null = $sb.AppendLine("    category: `"$cat`",")
    $null = $sb.AppendLine("    categoryEmoji: `"$emoji`",")
    $null = $sb.AppendLine("    categoryRange: `"$range`",")
    $null = $sb.AppendLine("    title: `"$escapedTitle`",")
    $null = $sb.AppendLine("    prompt: `"$escapedPrompt`",")
    $null = $sb.AppendLine("    tags: [$tagsJs]")
    $null = $sb.AppendLine("  }$comma")
}

$null = $sb.AppendLine("];")

[System.IO.File]::WriteAllText($outputFile, $sb.ToString(), [System.Text.Encoding]::UTF8)
Write-Host "✅ 완료! $($prompts.Count)개 프롬프트 -> ai_prompt_data.js" -ForegroundColor Green
