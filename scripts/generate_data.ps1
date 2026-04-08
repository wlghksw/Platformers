$csvPath = "$PSScriptRoot\..\data\sheet_1.csv"
$outputPath = "$PSScriptRoot\..\assets\js\connector_data.js"

# CSV 임포트 (헤더가 2줄에 걸쳐있어 수동 처리)
$raw = Get-Content $csvPath -Raw -Encoding UTF8

# 줄 단위로 분리
$lines = $raw -split "`r`n"

# 실제 데이터는 3번째 줄부터 (0-indexed: index 2)
$dataLines = $lines[2..($lines.Count - 1)] | Where-Object { $_ -match '^\d+,' }

function Parse-CSVLine($line) {
    $result = @()
    $current = ""
    $inQuotes = $false
    
    for ($i = 0; $i -lt $line.Length; $i++) {
        $char = $line[$i]
        if ($char -eq '"') {
            if ($inQuotes -and $i + 1 -lt $line.Length -and $line[$i+1] -eq '"') {
                $current += '"'
                $i++
            } else {
                $inQuotes = !$inQuotes
            }
        } elseif ($char -eq ',' -and !$inQuotes) {
            $result += $current
            $current = ""
        } else {
            $current += $char
        }
    }
    $result += $current
    return $result
}

function Escape-JS($str) {
    if ($null -eq $str) { return "" }
    $str = $str.Replace('\', '\\')
    $str = $str.Replace('"', '\"')
    $str = $str.Replace("`n", '\n')
    $str = $str.Replace("`r", '')
    return $str
}

function Split-Items($str) {
    if ([string]::IsNullOrEmpty($str) -or $str -eq '-') { return @() }
    # 쉼표 또는 가운뎃점(·)으로 분리
    $items = $str -split '[,·]' | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' -and $_ -ne '-' }
    return $items
}

function Build-SearchTags($nameEn, $nameKo, $category, $triggers, $actions, $desc) {
    $tags = @()
    # 이름
    if ($nameEn) { $tags += $nameEn.ToLower() }
    if ($nameKo) { $tags += $nameKo }
    # 카테고리
    if ($category) { $tags += $category }
    # 트리거/액션 분해
    foreach ($t in $triggers) { if ($t) { $tags += $t } }
    foreach ($a in $actions) { if ($a) { $tags += $a } }
    # 설명
    if ($desc) { $tags += $desc }
    # 중복 제거 및 빈 값 제거
    $tags = $tags | Where-Object { $_ -ne '' -and $_ -ne '-' } | Select-Object -Unique
    return $tags
}

$connectors = @()
$id = 0

foreach ($line in $dataLines) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    
    $fields = Parse-CSVLine $line
    if ($fields.Count -lt 9) { continue }
    
    $num       = $fields[0].Trim()
    $category  = $fields[1].Trim()
    $nameEn    = $fields[2].Trim()
    $nameKo    = $fields[3].Trim()
    $tier      = $fields[4].Trim()
    $trigStr   = $fields[5].Trim()
    $actStr    = $fields[6].Trim()
    # $suitability = $fields[7] -- 제거됨
    $desc      = $fields[8].Trim()
    
    $triggers = Split-Items $trigStr
    $actions  = Split-Items $actStr
    $tags     = Build-SearchTags $nameEn $nameKo $category $triggers $actions $desc
    
    # JS 배열 문자열 생성
    $triggersJS = ($triggers | ForEach-Object { "`"$(Escape-JS $_)`"" }) -join ", "
    $actionsJS  = ($actions  | ForEach-Object { "`"$(Escape-JS $_)`"" }) -join ", "
    $tagsJS     = ($tags     | ForEach-Object { "`"$(Escape-JS $_)`"" }) -join ", "
    
    $obj = @"
  {
    id: $num,
    category: "$(Escape-JS $category)",
    nameEn: "$(Escape-JS $nameEn)",
    nameKo: "$(Escape-JS $nameKo)",
    tier: "$(Escape-JS $tier)",
    triggers: [$triggersJS],
    actions: [$actionsJS],
    description: "$(Escape-JS $desc)",
    searchTags: [$tagsJS]
  }
"@
    $connectors += $obj
    $id++
}

$jsContent = @"
// Power Automate Connector Data
// Generated from PowerAutomate_connecter.xlsx
// Total: $($connectors.Count) connectors

const CONNECTORS = [
$($connectors -join ",`n")
];
"@

[System.IO.File]::WriteAllText($outputPath, $jsContent, [System.Text.Encoding]::UTF8)
Write-Host "완료: $($connectors.Count)개 커넥터 → connector_data.js 생성"
