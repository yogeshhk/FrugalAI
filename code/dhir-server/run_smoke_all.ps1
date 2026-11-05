# Runs the smoke test for each precision, one after another (they must not overlap: timings would be wrong).
# Usage from this folder:  powershell -File run_smoke_all.ps1 "C:\path\to\dhir-2b"
param([string]$ModelDir = $env:DHIR_MODEL_DIR)
$env:DHIR_MODEL_DIR = $ModelDir
$env:PYTHONIOENCODING = "utf-8"
foreach ($d in "bf16", "fp32", "int8") {
    Write-Output "=== $d"
    conda run -n genai python smoke.py --dtype $d
}
