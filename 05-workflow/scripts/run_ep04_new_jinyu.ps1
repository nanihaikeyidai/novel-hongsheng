$ErrorActionPreference = 'Stop'

$secretPath = 'C:\Users\Administrator\.codex\secrets\runninghub-api-key.dpapi'
$runner = Join-Path $PSScriptRoot 'run_ep04_new_jinyu.py'
$runnerArgs = $args

$env:PYTHONUTF8 = '1'
$secure = ConvertTo-SecureString (Get-Content -Raw -LiteralPath $secretPath)
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try {
    $env:RUNNINGHUB_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
}

& python $runner @runnerArgs
