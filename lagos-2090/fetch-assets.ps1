# Lagos 2090 — download 4K textures, HDRIs and high-detail Poly Haven models,
# then convert those models to Unreal-ready FBX with headless Blender.
#
# Run from this folder (C:\lagos-2090):
#   powershell -ExecutionPolicy Bypass -File .\fetch-assets.ps1
#
# Options:
#   -Force          Re-download even if the file already exists
#   -SkipConvert    Do not run Blender
#   -BlenderPath    Path to blender.exe
#   -VerifyOnly     Only check that assets-manifest.json paths exist
#   -Only <text>    Only fetch entries whose path contains this string (repeatable)

[CmdletBinding()]
param(
    [string]$Root,
    [switch]$Force,
    [switch]$SkipConvert,
    [string]$BlenderPath,
    [switch]$VerifyOnly,
    [string[]]$Only
)

$ErrorActionPreference = "Stop"
$UserAgent = "Lagos2090Pack/1.0 (CC0 fetch; https://polyhaven.com / https://ambientcg.com)"

if (-not $Root) {
    $Root = Split-Path -Parent $MyInvocation.MyCommand.Path
}
$Root = (Resolve-Path $Root).Path

function Write-Log($msg) { Write-Host $msg }

function Wanted([string]$key) {
    if (-not $Only -or $Only.Count -eq 0) { return $true }
    foreach ($s in $Only) {
        if ($key.ToLower().Contains($s.ToLower())) { return $true }
    }
    return $false
}

function Get-JsonFile($path) {
    return (Get-Content -Raw -Path $path | ConvertFrom-Json)
}

function Invoke-Download([string]$Url, [string]$Dest, [switch]$ForceThis) {
    $dir = Split-Path -Parent $Dest
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    if ((Test-Path $Dest) -and ((Get-Item $Dest).Length -gt 0) -and -not $ForceThis -and -not $Force) {
        $kb = [math]::Round((Get-Item $Dest).Length / 1KB)
        Write-Log "  exists $Dest ($kb KB)"
        return (Get-Item $Dest).Length
    }
    $tmp = "$Dest.part"
    $tries = 4
    for ($i = 1; $i -le $tries; $i++) {
        try {
            if (Test-Path $tmp) { Remove-Item $tmp -Force }
            $headers = @{ "User-Agent" = $UserAgent }
            Invoke-WebRequest -Uri $Url -OutFile $tmp -Headers $headers -UseBasicParsing -TimeoutSec 300
            Move-Item -Force $tmp $Dest
            return (Get-Item $Dest).Length
        } catch {
            Write-Log "  retry $i/$tries $(Split-Path -Leaf $Dest): $_"
            if (Test-Path $tmp) { Remove-Item $tmp -Force }
            Start-Sleep -Seconds (2 * $i)
            if ($i -eq $tries) { throw }
        }
    }
}

function Get-RemoteJson([string]$Url) {
    $headers = @{ "User-Agent" = $UserAgent }
    return Invoke-RestMethod -Uri $Url -Headers $headers -TimeoutSec 60
}

function Find-Blender([string]$Explicit) {
    if ($Explicit -and (Test-Path $Explicit)) { return $Explicit }
    if ($env:BLENDER -and (Test-Path $env:BLENDER)) { return $env:BLENDER }
    if ($env:BLENDER_PATH -and (Test-Path $env:BLENDER_PATH)) { return $env:BLENDER_PATH }
    $cmd = Get-Command blender -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $bases = @(${env:ProgramFiles}, ${env:ProgramFiles(x86)}, ${env:LOCALAPPDATA})
    foreach ($base in $bases) {
        if (-not $base) { continue }
        $found = Get-ChildItem -Path (Join-Path $base "Blender Foundation") -Filter "blender.exe" -Recurse -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($found) { return $found.FullName }
    }
    return $null
}

function Test-Manifest {
    param($Assets, $Fetch, [bool]$RequireFbx)
    $expected = New-Object System.Collections.Generic.List[string]
    foreach ($a in $Assets.assets) {
        foreach ($key in @("path", "path_glb", "path_fbx", "path_gltf")) {
            $p = $a.$key
            if (-not $p) { continue }
            if ($p.EndsWith("/")) {
                if ($a.maps) {
                    foreach ($name in $a.maps) { $expected.Add(($p + $name)) }
                }
                continue
            }
            $expected.Add($p)
        }
    }
    foreach ($item in $Fetch.hdris) { $expected.Add($item.path) }
    foreach ($item in $Fetch.textures) {
        foreach ($name in $item.keep) {
            $expected.Add(($item.dest.TrimEnd("/") + "/" + $name))
        }
    }
    foreach ($item in $Fetch.models) {
        if ($item.path_gltf) { $expected.Add($item.path_gltf) }
        if ($RequireFbx -and $item.path_fbx) { $expected.Add($item.path_fbx) }
    }
    $unique = $expected | Select-Object -Unique
    if ($Only -and $Only.Count -gt 0) {
        $unique = $unique | Where-Object { Wanted $_ }
    }
    $missing = @()
    $present = 0
    foreach ($rel in $unique) {
        $full = Join-Path $Root ($rel -replace "/", [IO.Path]::DirectorySeparatorChar)
        if ((Test-Path $full) -and ((Get-Item $full).Length -gt 0)) {
            $present++
        } else {
            $missing += $rel
        }
    }
    Write-Log "VERIFY present=$present missing=$($missing.Count) (of $($unique.Count) checked)"
    foreach ($rel in $missing) { Write-Log "  MISSING $rel" }
    return $missing
}

$fetchPath = Join-Path $Root "fetch-manifest.json"
$assetsPath = Join-Path $Root "assets-manifest.json"
if (-not (Test-Path $fetchPath) -or -not (Test-Path $assetsPath)) {
    Write-Log "ERROR cannot find fetch-manifest.json / assets-manifest.json in $Root"
    exit 2
}
$Fetch = Get-JsonFile $fetchPath
$Assets = Get-JsonFile $assetsPath

if ($VerifyOnly) {
    $missing = Test-Manifest $Assets $Fetch (-not $SkipConvert)
    if ($missing.Count -gt 0) { exit 1 } else { exit 0 }
}

$failures = @()

# HDRIs
foreach ($item in $Fetch.hdris) {
    if (-not (Wanted $item.path)) { continue }
    Write-Log "HDRI $($item.path)"
    try {
        $size = Invoke-Download $item.url (Join-Path $Root ($item.path -replace "/", [IO.Path]::DirectorySeparatorChar))
        Write-Log ("  wrote {0:N2} MB" -f ($size / 1MB))
    } catch {
        Write-Log "  FAIL $_"
        $failures += $item.path
    }
}

# Textures
$staging = Join-Path $env:TEMP ("lagos-tex-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $staging -Force | Out-Null
try {
    foreach ($item in $Fetch.textures) {
        if (-not (Wanted $item.dest) -and -not (Wanted $item.id)) { continue }
        $out = Join-Path $Root ($item.dest.TrimEnd("/") -replace "/", [IO.Path]::DirectorySeparatorChar)
        $keep = @($item.keep)
        $already = $true
        foreach ($name in $keep) {
            $fp = Join-Path $out $name
            if (-not (Test-Path $fp) -or ((Get-Item $fp).Length -le 0)) { $already = $false }
        }
        if ($already -and -not $Force) {
            Write-Log "TEXTURE $($item.id) already complete -> $($item.dest)"
            continue
        }
        Write-Log "TEXTURE $($item.id) -> $($item.dest)"
        try {
            $zpath = Join-Path $staging $item.zip
            Invoke-Download $item.url $zpath -ForceThis
            if (-not (Test-Path $out)) { New-Item -ItemType Directory -Path $out -Force | Out-Null }
            Add-Type -AssemblyName System.IO.Compression.FileSystem
            $zip = [System.IO.Compression.ZipFile]::OpenRead($zpath)
            try {
                $entries = @{}
                foreach ($entry in $zip.Entries) {
                    if ($entry.Name) { $entries[$entry.Name] = $entry }
                }
                foreach ($name in $keep) {
                    if (-not $entries.ContainsKey($name)) {
                        throw "$($item.zip) is missing $name"
                    }
                    $target = Join-Path $out $name
                    $destStream = [System.IO.File]::Create($target)
                    try {
                        $srcStream = $entries[$name].Open()
                        try { $srcStream.CopyTo($destStream) } finally { $srcStream.Dispose() }
                    } finally { $destStream.Dispose() }
                }
            } finally { $zip.Dispose() }
            Write-Log "  kept $($keep.Count) maps"
            Remove-Item $zpath -Force -ErrorAction SilentlyContinue
        } catch {
            Write-Log "  FAIL $_"
            $failures += $item.dest
        }
    }
} finally {
    Remove-Item $staging -Recurse -Force -ErrorAction SilentlyContinue
}

# Poly Haven models via the public API
foreach ($item in $Fetch.models) {
    if (-not (Wanted $item.folder) -and -not (Wanted $item.slug)) { continue }
    $dest = Join-Path $Root ($item.folder -replace "/", [IO.Path]::DirectorySeparatorChar)
    $gltfRel = $item.path_gltf
    $gltfPath = if ($gltfRel) { Join-Path $Root ($gltfRel -replace "/", [IO.Path]::DirectorySeparatorChar) } else { $null }
    $marker = Join-Path $dest ".download-complete"
    if ((Test-Path $marker) -and $gltfPath -and (Test-Path $gltfPath) -and -not $Force) {
        Write-Log "MODEL $($item.slug) already downloaded -> $($item.folder)"
        continue
    }
    Write-Log "MODEL $($item.slug) $($item.res) -> $($item.folder)"
    try {
        $files = Get-RemoteJson "https://api.polyhaven.com/files/$($item.slug)"
        $info = Get-RemoteJson "https://api.polyhaven.com/info/$($item.slug)"
        $res = $item.res
        $node = $files.gltf.$res.gltf
        if (-not (Test-Path $dest)) { New-Item -ItemType Directory -Path $dest -Force | Out-Null }
        $gltfName = if ($gltfRel) { Split-Path -Leaf $gltfRel } else { "$($item.slug)_$res.gltf" }
        Invoke-Download $node.url (Join-Path $dest $gltfName)
        if ($node.include) {
            $node.include.PSObject.Properties | ForEach-Object {
                $rel = $_.Name
                $meta = $_.Value
                $target = Join-Path $dest ($rel -replace "/", [IO.Path]::DirectorySeparatorChar)
                Invoke-Download $meta.url $target
            }
        }
        $source = @{
            slug = $item.slug
            name = $info.name
            authors = $info.authors
            license = $item.license
            source = $item.source_page
            resolution = $item.res
            type = "model"
        }
        ($source | ConvertTo-Json -Depth 6) | Set-Content -Path (Join-Path $dest "SOURCE.json") -Encoding UTF8
        "ok" | Set-Content -Path $marker -Encoding UTF8
        Write-Log "  downloaded $($item.slug)"
    } catch {
        Write-Log "  FAIL $_"
        $failures += $item.folder
    }
}

$convertFailed = $false
if (-not $SkipConvert) {
    $blender = Find-Blender $BlenderPath
    if (-not $blender) {
        Write-Log "WARNING Blender not found. HD models were left as glTF."
        Write-Log "Install Blender, then re-run this script (it will skip files that already exist)."
        $convertFailed = $true
    } else {
        Write-Log "Using Blender: $blender"
        $script = Join-Path $Root "convert_hd_to_fbx.py"
        if (-not (Test-Path $script)) {
            Write-Log "WARNING convert_hd_to_fbx.py is missing; skip FBX conversion"
            $convertFailed = $true
        } else {
            $cmdArgs = @("--background", "--python", $script, "--", "--root", $Root)
            if ($Only -and $Only.Count -gt 0) {
                foreach ($item in $Fetch.models) {
                    if ((Wanted $item.folder) -or (Wanted $item.slug)) {
                        $cmdArgs += (Join-Path $Root ($item.folder -replace "/", [IO.Path]::DirectorySeparatorChar))
                    }
                }
            }
            Write-Log "CONVERT $blender $($cmdArgs -join ' ')"
            & $blender @cmdArgs
            if ($LASTEXITCODE -ne 0) {
                Write-Log "WARNING Blender conversion exited with $LASTEXITCODE"
                $convertFailed = $true
            }
        }
    }
}

$requireFbx = (-not $SkipConvert) -and (-not $convertFailed)
$missing = Test-Manifest $Assets $Fetch $requireFbx
if ($failures.Count -gt 0 -or $missing.Count -gt 0 -or $convertFailed) {
    Write-Log "DONE with issues. Fix the errors above and re-run."
    exit 1
}
Write-Log "DONE. Every requested manifest file is present."
exit 0
