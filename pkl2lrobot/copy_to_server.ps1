# Copy dataset to remote server via SCP
# Target: axgu@10.16.118.8:/data2/axgu/.cache

$LocalPath = ".\data\lrobot\move_cup_to_shelf"
$RemoteUser = "axgu"
$RemoteHost = "10.16.118.8"
$RemotePath = "/data2/axgu/.cache/huggingface/lerobot/luobai"

Write-Host "📦 Copying dataset to remote server..." -ForegroundColor Cyan
Write-Host "   Local:  $LocalPath" -ForegroundColor Gray
Write-Host "   Remote: ${RemoteUser}@${RemoteHost}:${RemotePath}" -ForegroundColor Gray
Write-Host ""

# Check if local path exists
if (-not (Test-Path $LocalPath)) {
    Write-Host "❌ Error: Local dataset not found at $LocalPath" -ForegroundColor Red
    exit 1
}

# Use SCP to copy recursively
# -r: recursive copy
# -p: preserve modification times and modes
# -C: enable compression
Write-Host "🚀 Starting transfer (this may take a while)..." -ForegroundColor Yellow

scp -r -p -C $LocalPath "${RemoteUser}@${RemoteHost}:${RemotePath}"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Dataset successfully copied to remote server!" -ForegroundColor Green
    Write-Host "   Remote path: ${RemotePath}" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "❌ Transfer failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    Write-Host "   Please check:" -ForegroundColor Yellow
    Write-Host "   - SSH connection to ${RemoteHost}" -ForegroundColor Gray
    Write-Host "   - Remote directory permissions" -ForegroundColor Gray
    Write-Host "   - Network connectivity" -ForegroundColor Gray
    exit 1
}
