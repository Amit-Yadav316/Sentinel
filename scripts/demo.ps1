# scripts/demo.ps1 — one-command offline demo for Windows.
# Seeds the calm state, launches the API + frontend in separate windows, waits
# for the backend to be healthy, and opens the dashboard. Then click
# "Run escalation demo" in the top bar to play the full loop.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

Write-Host "== Seeding calm demo state ==" -ForegroundColor Cyan
Push-Location $backend
uv run python -m app.seed.seed
Pop-Location

Write-Host "== Launching API on :8000 ==" -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
  "-NoExit", "-Command",
  "Set-Location '$backend'; uv run uvicorn app.main:app --port 8000"
)

Write-Host "== Launching frontend on :5173 ==" -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
  "-NoExit", "-Command",
  "Set-Location '$frontend'; npm run dev"
)

Write-Host "== Waiting for backend health ==" -ForegroundColor Cyan
$ok = $false
for ($i = 0; $i -lt 30; $i++) {
  try {
    $r = Invoke-RestMethod "http://localhost:8000/health" -TimeoutSec 2
    if ($r.status -eq "ok") { $ok = $true; break }
  } catch { Start-Sleep -Seconds 1 }
}
if ($ok) { Write-Host "Backend healthy." -ForegroundColor Green }
else { Write-Host "Backend not confirmed; continuing anyway." -ForegroundColor Yellow }

Start-Sleep -Seconds 3
Start-Process "http://localhost:5173"
Write-Host ""
Write-Host "Dashboard: http://localhost:5173" -ForegroundColor Green
Write-Host "Click 'Run escalation demo' (top-right) to play signal -> recommendation." -ForegroundColor Green
