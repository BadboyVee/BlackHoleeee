#!/usr/bin/env python3
"""Download the 4K textures, HDRIs and high-detail Poly Haven models excluded
from the lean Lagos 2090 pack, then convert those models to Unreal-ready FBX.

Run from the folder that contains this script and fetch-manifest.json:

    python fetch_assets.py

Options:
    --root PATH          Pack root (default: this script's folder)
    --only SUBSTRING     Only fetch entries whose path/folder contains this
                         (repeatable). Useful for testing.
    --force              Re-download even if the file already exists
    --skip-convert       Do not run Blender
    --blender PATH       Path to the blender executable
    --verify-only        Only check that assets-manifest.json paths exist
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path

UA = "Lagos2090Pack/1.0 (CC0 fetch; https://polyhaven.com / https://ambientcg.com)"


def log(msg: str) -> None:
    print(msg, flush=True)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def download(url: str, dest: Path, force: bool = False, retries: int = 4) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0 and not force:
        log(f"  exists {dest} ({dest.stat().st_size / 1024:.0f} KB)")
        return dest.stat().st_size
    tmp = dest.with_suffix(dest.suffix + ".part")
    last_err = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=300) as r, tmp.open("wb") as f:
                while True:
                    chunk = r.read(256 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
            tmp.replace(dest)
            return dest.stat().st_size
        except Exception as e:
            last_err = e
            if tmp.exists():
                tmp.unlink()
            log(f"  retry {i + 1}/{retries} {dest.name}: {e}")
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"failed to download {url}: {last_err}")


def get_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def wanted(entry_key: str, only: list[str]) -> bool:
    if not only:
        return True
    key = entry_key.lower()
    return any(s.lower() in key for s in only)


def fetch_hdris(root: Path, items, only, force) -> list[str]:
    failures = []
    for item in items:
        path = item["path"]
        if not wanted(path, only):
            continue
        log(f"HDRI {path}")
        try:
            size = download(item["url"], root / path, force=force)
            log(f"  wrote {size / 1024 / 1024:.2f} MB")
        except Exception as e:
            log(f"  FAIL {e}")
            failures.append(path)
    return failures


def fetch_textures(root: Path, items, only, force) -> list[str]:
    failures = []
    staging = Path(tempfile.mkdtemp(prefix="lagos-tex-"))
    try:
        for item in items:
            dest_rel = item["dest"]
            if not wanted(dest_rel, only) and not wanted(item["id"], only):
                continue
            out = root / dest_rel
            keep = list(item["keep"])
            already = all((out / name).exists() and (out / name).stat().st_size > 0 for name in keep)
            if already and not force:
                log(f"TEXTURE {item['id']} already complete -> {dest_rel}")
                continue
            log(f"TEXTURE {item['id']} -> {dest_rel}")
            try:
                zpath = staging / item["zip"]
                download(item["url"], zpath, force=True)
                out.mkdir(parents=True, exist_ok=True)
                kept = []
                with zipfile.ZipFile(zpath) as zf:
                    names = {Path(info.filename).name: info for info in zf.infolist() if not info.is_dir()}
                    for name in keep:
                        if name not in names:
                            raise RuntimeError(f"{item['zip']} is missing {name}")
                        target = out / name
                        with zf.open(names[name]) as src, target.open("wb") as dst:
                            shutil.copyfileobj(src, dst)
                        kept.append(name)
                log(f"  kept {len(kept)} maps")
                zpath.unlink(missing_ok=True)
            except Exception as e:
                log(f"  FAIL {e}")
                failures.append(dest_rel)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return failures


def fetch_models(root: Path, items, only, force) -> list[str]:
    failures = []
    for item in items:
        folder = item["folder"]
        if not wanted(folder, only) and not wanted(item["slug"], only):
            continue
        dest = root / folder
        gltf_rel = item.get("path_gltf") or ""
        gltf_path = root / gltf_rel if gltf_rel else None
        marker = dest / ".download-complete"
        if marker.exists() and gltf_path and gltf_path.exists() and not force:
            log(f"MODEL {item['slug']} already downloaded -> {folder}")
            continue
        log(f"MODEL {item['slug']} {item['res']} -> {folder}")
        try:
            files = get_json(f"https://api.polyhaven.com/files/{item['slug']}")
            info = get_json(f"https://api.polyhaven.com/info/{item['slug']}")
            node = files["gltf"][item["res"]]["gltf"]
            dest.mkdir(parents=True, exist_ok=True)
            gltf_name = Path(gltf_rel).name if gltf_rel else f"{item['slug']}_{item['res']}.gltf"
            download(node["url"], dest / gltf_name, force=force)
            for rel, meta in (node.get("include") or {}).items():
                download(meta["url"], dest / rel, force=force)
            (dest / "SOURCE.json").write_text(
                json.dumps(
                    {
                        "slug": item["slug"],
                        "name": info.get("name", item.get("name")),
                        "authors": info.get("authors") or {},
                        "license": item.get("license", "CC0 1.0"),
                        "source": item.get("source_page") or f"https://polyhaven.com/a/{item['slug']}",
                        "resolution": item["res"],
                        "type": "model",
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            marker.write_text("ok\n", encoding="utf-8")
            log(f"  downloaded {item['slug']}")
        except Exception as e:
            log(f"  FAIL {e}")
            failures.append(folder)
    return failures


def find_blender(explicit: str | None) -> str | None:
    if explicit:
        return explicit
    env = os.environ.get("BLENDER") or os.environ.get("BLENDER_PATH")
    if env and Path(env).exists():
        return env
    which = shutil.which("blender")
    if which:
        return which
    # Common Windows and Linux install locations
    candidates = []
    pf = os.environ.get("ProgramFiles", r"C:\Program Files")
    pfx86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    for base in (pf, pfx86):
        foundation = Path(base) / "Blender Foundation"
        if foundation.exists():
            candidates.extend(foundation.glob("Blender */blender.exe"))
    candidates.extend(
        [
            Path("/home/box/tools/blender-4.5.16-linux-x64/blender"),
            Path("/usr/bin/blender"),
            Path("/usr/local/bin/blender"),
        ]
    )
    for c in candidates:
        if Path(c).exists():
            return str(c)
    return None


def convert_hd(root: Path, blender: str, only: list[str]) -> int:
    script = root / "convert_hd_to_fbx.py"
    if not script.exists():
        log("WARNING convert_hd_to_fbx.py is missing; skip FBX conversion")
        return 1
    cmd = [blender, "--background", "--python", str(script), "--", "--root", str(root)]
    if only:
        # Pass matching hd folders so we don't reconvert the whole pack in a test
        fm = load_json(root / "fetch-manifest.json")
        for item in fm["models"]:
            key = item["folder"]
            if wanted(key, only) or wanted(item["slug"], only):
                cmd.append(str(root / item["folder"]))
    log("CONVERT with " + " ".join(cmd))
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        log(f"WARNING Blender conversion exited with {result.returncode}")
        return result.returncode
    return 0


def expected_paths(root: Path, assets_manifest, fetch_manifest, require_fbx: bool):
    """Paths that must exist after a full fetch + convert."""
    expected = []
    # Bundled Kenney / font / docs already in the lean pack
    for a in assets_manifest["assets"]:
        for key in ("path", "path_glb", "path_fbx", "path_gltf"):
            p = a.get(key)
            if not p:
                continue
            if p.endswith("/"):
                # directory entry: require listed maps, or gltf/fbx if present
                if a.get("maps"):
                    for name in a["maps"]:
                        expected.append(p + name)
                continue
            expected.append(p)
    # Always require fetch-manifest targets
    for item in fetch_manifest["hdris"]:
        expected.append(item["path"])
    for item in fetch_manifest["textures"]:
        for name in item["keep"]:
            expected.append(item["dest"].rstrip("/") + "/" + name)
    for item in fetch_manifest["models"]:
        if item.get("path_gltf"):
            expected.append(item["path_gltf"])
        if require_fbx and item.get("path_fbx"):
            expected.append(item["path_fbx"])
    # unique, keep order
    seen = set()
    out = []
    for p in expected:
        p = p.replace("\\", "/")
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def verify(root: Path, assets_manifest, fetch_manifest, require_fbx: bool, only: list[str]):
    paths = expected_paths(root, assets_manifest, fetch_manifest, require_fbx)
    if only:
        paths = [p for p in paths if wanted(p, only)]
    missing = []
    present = 0
    for rel in paths:
        p = root / rel
        if p.exists() and p.stat().st_size > 0:
            present += 1
        else:
            missing.append(rel)
    log(f"VERIFY present={present} missing={len(missing)} (of {len(paths)} checked)")
    for rel in missing:
        log(f"  MISSING {rel}")
    return missing


def main():
    parser = argparse.ArgumentParser(description="Fetch Lagos 2090 textures, HDRIs and HD models")
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--only", action="append", default=[])
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--skip-convert", action="store_true")
    parser.add_argument("--blender", default=None)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()

    root = (args.root or Path(__file__).resolve().parent).resolve()
    fetch_path = root / "fetch-manifest.json"
    assets_path = root / "assets-manifest.json"
    if not fetch_path.exists() or not assets_path.exists():
        log(f"ERROR cannot find fetch-manifest.json / assets-manifest.json in {root}")
        sys.exit(2)
    fetch = load_json(fetch_path)
    assets = load_json(assets_path)

    if args.verify_only:
        missing = verify(root, assets, fetch, require_fbx=not args.skip_convert, only=args.only)
        sys.exit(1 if missing else 0)

    failures = []
    failures += fetch_hdris(root, fetch["hdris"], args.only, args.force)
    failures += fetch_textures(root, fetch["textures"], args.only, args.force)
    failures += fetch_models(root, fetch["models"], args.only, args.force)

    convert_failed = False
    if not args.skip_convert:
        blender = find_blender(args.blender)
        if not blender:
            log("WARNING Blender not found. HD models were left as glTF.")
            log("Install Blender, then re-run this script (it will skip files that already exist).")
            convert_failed = True
        else:
            log(f"Using Blender: {blender}")
            if convert_hd(root, blender, args.only) != 0:
                convert_failed = True

    missing = verify(
        root,
        assets,
        fetch,
        require_fbx=not args.skip_convert and not convert_failed,
        only=args.only,
    )
    if failures or missing or convert_failed:
        log("DONE with issues. Fix the errors above and re-run.")
        sys.exit(1)
    log("DONE. Every requested manifest file is present.")
    return 0


if __name__ == "__main__":
    main()
