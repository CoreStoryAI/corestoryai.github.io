# Install the CoreStory command-line tool on Windows (x64).
#
#   irm https://get.corestory.ai/install.ps1 | iex
#
# Downloads the newest release from github.com/CoreStory-Frontier/release-dist,
# checks its SHA-256, puts corestory.exe in %LOCALAPPDATA%\CoreStory\bin (or
# $env:CORESTORY_INSTALL_DIR) and adds that folder to your user PATH.
# It does not accept the terms of use or send telemetry: run `corestory setup` next.
# Needs Windows 10 (1803) or later, which ships tar.exe.

& {
  $ErrorActionPreference = 'Stop'
  $ProgressPreference = 'SilentlyContinue'   # Invoke-WebRequest is very slow with the progress bar on
  [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12

  $repo = 'CoreStory-Frontier/release-dist'
  $releasesUrl = if ($env:CORESTORY_RELEASES_URL) { $env:CORESTORY_RELEASES_URL } else { "https://api.github.com/repos/$repo/releases?per_page=10" }
  $installDir = if ($env:CORESTORY_INSTALL_DIR) { $env:CORESTORY_INSTALL_DIR } else { Join-Path $env:LOCALAPPDATA 'CoreStory\bin' }

  function Fail($msg) { Write-Host "corestory install: $msg" -ForegroundColor Red; throw "corestory install failed" }

  $arch = if ($env:CORESTORY_TEST_ARCH) { $env:CORESTORY_TEST_ARCH } else { $env:PROCESSOR_ARCHITECTURE }
  if ($arch -ne 'AMD64') { Fail "only 64-bit x64 Windows is supported yet (this machine reports $arch). See https://get.corestory.ai" }
  if (-not (Get-Command tar -ErrorAction SilentlyContinue)) { Fail "needs tar.exe (Windows 10 1803 or later). Download by hand: https://github.com/$repo/releases" }

  try {
    $releases = Invoke-RestMethod -Uri $releasesUrl -Headers @{ Accept = 'application/vnd.github+json' } -UseBasicParsing
  } catch { Fail "couldn't reach GitHub to find the latest release. Download by hand: https://github.com/$repo/releases" }

  $asset = $null
  foreach ($r in @($releases)) {
    if ($r.draft) { continue }
    $asset = $r.assets | Where-Object { $_.name -match '^corestory-cli-.+-x86_64-pc-windows-gnu\.(tar\.gz|zip)$' } | Select-Object -First 1
    if ($asset) { break }
  }
  if (-not $asset) { Fail "no Windows command-line tool in the latest release. See https://github.com/$repo/releases" }

  $tmp = Join-Path ([IO.Path]::GetTempPath()) ("corestory-" + [Guid]::NewGuid().ToString('N'))
  New-Item -ItemType Directory -Path $tmp | Out-Null
  try {
    $file = Join-Path $tmp $asset.name
    Write-Host "Downloading $($asset.name)"
    Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $file -UseBasicParsing
    $shaText = (Invoke-WebRequest -Uri ($asset.browser_download_url + '.sha256') -UseBasicParsing).Content
    if ($shaText -is [byte[]]) { $shaText = [Text.Encoding]::ASCII.GetString($shaText) }
    # The .sha256 file names a build path, so compare the hash field only.
    $want = ($shaText.Trim() -split '\s+')[0].ToLowerInvariant()
    $got = (Get-FileHash -Algorithm SHA256 -Path $file).Hash.ToLowerInvariant()
    if (-not $want -or $want -ne $got) { Fail "checksum mismatch for $($asset.name) (expected $want, got $got). Nothing was installed." }

    if ($asset.name -like '*.zip') { Expand-Archive -Path $file -DestinationPath $tmp -Force }
    else { & tar -xzf $file -C $tmp; if ($LASTEXITCODE -ne 0) { Fail "couldn't unpack $($asset.name)" } }
    $exe = Join-Path $tmp 'bin\corestory.exe'
    if (-not (Test-Path $exe)) { $exe = Join-Path $tmp 'bin/corestory.exe' }
    if (-not (Test-Path $exe)) { Fail "the archive has no bin\corestory.exe" }

    New-Item -ItemType Directory -Force -Path $installDir | Out-Null
    $dest = Join-Path $installDir 'corestory.exe'
    try { Copy-Item -Path $exe -Destination $dest -Force; (Get-Item $dest).IsReadOnly = $false }
    catch { Fail "couldn't write $dest. If CoreStory is running (for example as an MCP server), close it and try again." }
  } finally {
    Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
  }

  $version = try { (& $dest --version 2>$null) | Select-Object -First 1 } catch { $null }
  Write-Host ""
  Write-Host "Installed $(if ($version) { $version } else { 'corestory' }) to $dest"

  # Add to the user PATH (persisted) and to this session.
  $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
  $parts = @($userPath -split ';' | Where-Object { $_ })
  if ($parts -notcontains $installDir) {
    if ($env:CORESTORY_TEST_NO_PATH) { Write-Host "(test: would add $installDir to the user PATH)" }
    else {
      [Environment]::SetEnvironmentVariable('Path', (($parts + $installDir) -join ';'), 'User')
      Write-Host "Added $installDir to your user PATH. Open a new terminal to pick it up."
    }
  }
  if (($env:Path -split ';') -notcontains $installDir) { $env:Path = "$env:Path;$installDir" }

  Write-Host ""
  Write-Host "Next: run 'corestory setup' to accept the terms of use, choose telemetry and add a model key."
  Write-Host "Setup guide: https://get.corestory.ai/#setup"
}
