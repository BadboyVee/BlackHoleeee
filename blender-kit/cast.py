"""The recurring cast, with fixed looks: a mixed group of black and white men and women."""
import mh

SAND, OLIVE, RUST, WHITE, MUSTARD, KHAKI, STONE, NAVY, SKY, CREAM, CHARCOAL, TEAL, WINE = (
    (0.78, 0.66, 0.48), (0.36, 0.4, 0.24), (0.7, 0.3, 0.17), (0.92, 0.92, 0.9), (0.85, 0.62, 0.18),
    (0.66, 0.57, 0.42), (0.6, 0.58, 0.54), (0.1, 0.14, 0.26), (0.55, 0.7, 0.88), (0.9, 0.85, 0.74),
    (0.2, 0.2, 0.22), (0.12, 0.42, 0.45), (0.45, 0.1, 0.16))
BROWN_HAIR, BLOND, BLACK_HAIR, AUBURN = (0.5, 0.75, 0.55), (0.5, 0.9, 1.0), (0.5, 0.3, 0.3), (0.5, 0.9, 0.6)

CAST = {
    # ---- the Sahara crew: three men, two women
    "tunde": dict(gender="male", race="african", hair="short04", expression="smile",
                  clothes=["namuhekam_male_polo_shirt", "toigo_wool_pants", "toigo_ankle_boots_male"],
                  retint={"toigo_wool_pants": dict(whole=KHAKI)}),
    "jack": dict(gender="male", race="caucasian", hair="cortu_short_messy_hair", expression="grin",
                 clothes=["elvs_male_shirt_untucked_bd1", "toigo_wool_pants", "culturalibre_male_boots"],
                 retint={"elvs_male_shirt_untucked_bd1": dict(whole=SKY), "toigo_wool_pants": dict(whole=STONE)},
                 tint={"cortu_short_messy_hair": BROWN_HAIR}),
    "emeka": dict(gender="male", race="african", hair="afro01", expression="soft",
                  clothes=["elvs_male_boho_top1", "toigo_wool_pants", "culturalibre_sneakers"],
                  retint={"elvs_male_boho_top1": dict(whole=CREAM), "toigo_wool_pants": dict(whole=OLIVE)}),
    "amina": dict(gender="female", race="african", hair="elvs_reverse_french_braid_bun", expression="smile",
                  clothes=["mindfront_knitted_sweater_02", "toigo_harem_pants", "toigo_ballet_flats"],
                  retint={"mindfront_knitted_sweater_02": dict(whole=MUSTARD)}),
    "sophie": dict(gender="female", race="caucasian", hair="toigo_inverted_bob", expression="grin",
                   clothes=["punkduck_off-shoulder_long-sleeve_top", "toigo_wool_pants", "toigo_ankle_boots_female"],
                   retint={"toigo_wool_pants": dict(whole=SAND)}, tint={"toigo_inverted_bob": BLOND}),
    # ---- at the house
    "ngozi": dict(gender="female", race="african", hair="elvs_reverse_french_braid_bun", expression="smile",
                  clothes=["toigo_female_suit", "mindfront_shoes_oxford_female"]),
    "bayo": dict(gender="male", race="african", hair="short04", expression="soft",
                 clothes=["toigo_male_suit_3", "mindfront_shoes_oxford_male"]),
    "claire": dict(gender="female", race="caucasian", hair="elvs_wavy_bob", expression="smile",
                   clothes=["punkduck_lace_up_blouse", "toigo_long_full_skirt", "toigo_ballet_flats"],
                   tint={"elvs_wavy_bob": AUBURN}),
    "mark": dict(gender="male", race="caucasian", hair="elvs_grump_hair", expression="smile",
                 clothes=["namuhekam_male_polo_shirt", "toigo_wool_pants", "mindfront_shoes_oxford_male"],
                 retint={"toigo_wool_pants": dict(whole=NAVY)}, tint={"elvs_grump_hair": BROWN_HAIR}),
    "zainab": dict(gender="female", race="african", hair="elvs_micky_afro", expression="grin",
                   clothes=["toigo_camisole_top", "frankyaye_mini_skirt_01", "dressupdoc_sandals1"]),
    "lena": dict(gender="female", race="caucasian", hair="elvs_hazel_hair", expression="soft",
                 clothes=["mindfront_knitted_sweater_01", "toigo_wool_pants", "toigo_ankle_boots_female"],
                 retint={"toigo_wool_pants": dict(whole=CHARCOAL)}, tint={"elvs_hazel_hair": BROWN_HAIR}),
    "kunle": dict(gender="male", race="african", hair="short01", expression="neutral",
                  clothes=["male_worksuit01", "shoes04"]),
    "guard": dict(gender="male", race="african", hair="short04", expression="neutral",
                  clothes=["elvs_male_shirt_tie_tucked1", "toigo_wool_pants", "mindfront_shoes_oxford_male"],
                  retint={"elvs_male_shirt_tie_tucked1": dict(whole=SKY), "toigo_wool_pants": dict(whole=NAVY)}),
}


def make(name, pose="stand", collection=None, obj_name=None, **over):
    spec = dict(CAST[name])
    rt = spec.pop("retint", {})
    tex = {a: mh.retint(a, name, **kw) for a, kw in rt.items()}
    spec.update(over)
    p = mh.POSES[pose] if isinstance(pose, str) else pose
    return mh.human(obj_name or name, pose=p, collection=collection, textures=tex, **spec)
