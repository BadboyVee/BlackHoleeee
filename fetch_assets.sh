#!/bin/bash
# Downloads every third-party asset the two Blender scenes use into $ASSETS
# (default /home/user/assets). Poly Haven textures/models/skies are fetched on
# demand by blender-kit/ph.py, so they are not listed here.
# Needs: pip install bpy==5.3.0 DracoPy numpy pillow
set -u
A=${ASSETS:-/home/user/assets}
UA="blender-scene-builder"
HERE="$(cd "$(dirname "$0")" && pwd)"
get() { [ -s "$2" ] || { mkdir -p "$(dirname "$2")"; for t in 1 2 3 4 5; do curl -sfL --http1.1 -A "$UA" -o "$2" "$1" && break; sleep 3; done; }; }

# --- cars
get https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/models/gltf/ferrari.glb "$A/cars/ferrari.glb"
get https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/CarConcept/glTF-Binary/CarConcept.glb "$A/cars/CarConcept.glb"
[ -s "$A/cars/ferrari_plain.glb" ] || python3 "$HERE/blender-kit/undraco.py" "$A/cars/ferrari.glb" "$A/cars/ferrari_plain.glb"
[ -s "$A/cars/CarConcept_plain.glb" ] || python3 "$HERE/blender-kit/undraco.py" "$A/cars/CarConcept.glb" "$A/cars/CarConcept_plain.glb"
get https://download.blender.org/demo/test/BMW27_2.blend.zip "$A/cars/bmw/bmw.zip"
[ -d "$A/cars/bmw/bmw27" ] || unzip -q -o "$A/cars/bmw/bmw.zip" -d "$A/cars/bmw"
GZ=https://raw.githubusercontent.com/osrf/gazebo_models/master
for f in suv/meshes/suv.obj suv/meshes/suv.mtl suv/materials/textures/suv.png suv/materials/textures/wheels_01.png \
         hatchback/meshes/hatchback.obj hatchback/meshes/hatchback.mtl hatchback/materials/textures/hatchback.png hatchback/materials/textures/wheels3.png \
         prius_hybrid/meshes/Hybrid.obj prius_hybrid/meshes/Hybrid.mtl prius_hybrid/materials/textures/Hybrid.png \
         prius_hybrid/materials/textures/Hybrid_Interior.png prius_hybrid/materials/textures/Wheels3.png; do
  get "$GZ/$f" "$A/cars/gz/$f"
done

# --- people: MakeHuman base mesh / rig (inside the MPFB extension) and asset packs
get "https://extensions.blender.org/download/sha256:c075b3e9b94b8e5556a5f03f4653602d02ea306de08126e8f55ed6dee28a2dad/add-on-mpfb-v2.0.18.zip" "$A/mh/mpfb.zip"
[ -d "$A/mh/mpfb_ext" ] || unzip -q -o "$A/mh/mpfb.zip" -d "$A/mh/mpfb_ext"     # only its data/ folder is read; the add-on is not installed
MHF=https://files.makehumancommunity.org/asset_packs
get "$MHF/makehuman_system_assets/makehuman_system_assets_cc0.zip" "$A/mh/sys.zip"
[ -d "$A/mh/sys" ] || unzip -q -o "$A/mh/sys.zip" -d "$A/mh/sys"
for spec in hair01:cc0 hair02:ccby shirts01:cc0 shirts02:ccby shirts03:ccby pants01:cc0 suits01:cc0 shoes01:cc0 shoes02:ccby \
            skins02:cc0 skins03:cc0 hats01:cc0 glasses01:cc0 skirts01:cc0 eyebrows01:cc0; do
  p=${spec%%:*}; l=${spec##*:}
  get "$MHF/$p/${p}_$l.zip" "$A/mh/packs/$p.zip"
  [ -d "$A/mh/ext_$p" ] || unzip -q -o "$A/mh/packs/$p.zip" -d "$A/mh/ext_$p"
done
echo "assets ready in $A"
