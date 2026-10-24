param(
    [string]$Suffix = ""
)

$ErrorActionPreference = 'Stop'

$secretPath = 'C:\Users\Administrator\.codex\secrets\runninghub-api-key.dpapi'
$runner = Join-Path $PSScriptRoot 'run_ep04_s16_cuiyu.py'

$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$secure = ConvertTo-SecureString (Get-Content -Raw -LiteralPath $secretPath)
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try {
    $env:RUNNINGHUB_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
}

$runnerArgs = @()
if ($Suffix) {
    $runnerArgs += @('--suffix', $Suffix)
}

& python $runner @runnerArgs
