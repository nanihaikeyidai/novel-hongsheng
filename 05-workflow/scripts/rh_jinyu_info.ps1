param(
    [string]$AppId = '2093984226331938818'
)

$ErrorActionPreference = 'Stop'

$secretPath = 'C:\Users\Administrator\.codex\secrets\runninghub-api-key.dpapi'
$runner = 'C:\Users\Administrator\.codex\skills\runninghub\scripts\runninghub_app.py'

$env:PYTHONUTF8 = '1'
$secure = ConvertTo-SecureString (Get-Content -Raw -LiteralPath $secretPath)
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try {
    $env:RUNNINGHUB_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
}

& python $runner --info $AppId
