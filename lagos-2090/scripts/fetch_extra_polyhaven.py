#!/usr/bin/env python3
"""Fetch extra CC0 Poly Haven models (and a few textures) used by the Blender
build beyond the lean pack's manifest. Everything lands in models/extra/hd-<slug>/
(or textures/extra/<slug>/) with a SOURCE.json recording author and licence.

    python scripts/fetch_extra_polyhaven.py
"""
import json, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = "Lagos2090Pack/1.0 (CC0 fetch; https://polyhaven.com)"

MODELS = {  # slug: resolution
    "island_tree_01": "1k", "island_tree_02": "1k", "island_tree_03": "1k",
    "jacaranda_tree": "1k", "tree_small_02": "1k", "pachira_aquatica_01": "1k",
    "shrub_02": "1k", "shrub_03": "1k", "shrub_04": "1k",
    "anthurium_botany_01": "1k", "weed_plant_02": "1k", "nettle_plant": "1k",
    "potted_plant_04": "1k", "planter_box_02": "1k", "grass_medium_02": "1k",
    "concrete_road_barrier": "1k", "covered_car": "1k",
    "plastic_monobloc_chair_01": "1k", "plastic_jerrycan": "1k",
    "portable_generator": "1k", "wicker_basket_01": "1k", "wicker_basket_02": "1k",
    "plastic_crate_02": "1k", "plastic_crate_03": "1k", "rusted_wheel_rim_01": "1k",
    "small_lpg_tank": "1k", "rollershutter_door": "1k", "rollershutter_window_01": "1k",
    "modular_pipes": "1k", "water_manhole_cover": "1k", "cement_bag": "1k",
    "trashbag": "1k", "painted_wooden_stool": "1k", "painted_wooden_table": "1k",
    "sweet_potato": "1k", "food_pomegranate_01": "1k", "plastic_bottle_gallon": "1k",
    "plastic_container": "1k", "industrial_pastic_container": "1k", "Barrel_02": "1k",
    "street_lamp_02": "1k", "outdoor_table_chair_set_01": "1k", "hand_truck": "1k",
    "food_kiwi_01": "1k", "food_pears_asian_01": "1k", "wooden_bucket_01": "1k",
}
TEXTURES = {  # slug: (resolution, maps)
}


def get(url, binary=False, retries=4):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=300) as r:
                data = r.read()
            return data if binary else json.loads(data.decode())
        except Exception as e:  # noqa
            err = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"{url}: {err}")


def fetch_model(slug, res):
    dest = ROOT / "models" / "extra" / ("hd-" + slug.lower().replace("_", "-"))
    if (dest / ".download-complete").exists():
        return "cached"
    files = get(f"https://api.polyhaven.com/files/{slug}")
    info = get(f"https://api.polyhaven.com/info/{slug}")
    if res not in files["gltf"]:
        res = sorted(files["gltf"].keys())[0]
    node = files["gltf"][res]["gltf"]
    dest.mkdir(parents=True, exist_ok=True)
    (dest / f"{slug}_{res}.gltf").write_bytes(get(node["url"], binary=True))
    for rel, meta in (node.get("include") or {}).items():
        p = dest / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(get(meta["url"], binary=True))
    (dest / "SOURCE.json").write_text(json.dumps({
        "slug": slug, "name": info.get("name"), "authors": info.get("authors") or {},
        "license": "CC0 1.0", "source": f"https://polyhaven.com/a/{slug}",
        "resolution": res, "type": "model"}, indent=2) + "\n")
    (dest / ".download-complete").write_text("ok\n")
    return "ok"


def main():
    bad = 0
    for slug, res in MODELS.items():
        try:
            print(slug, fetch_model(slug, res), flush=True)
        except Exception as e:
            bad += 1
            print(slug, "FAIL", e, flush=True)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
