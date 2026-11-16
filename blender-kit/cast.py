"""The recurring cast, with fixed looks: a mixed group of black and white men and women."""
import mh

SAND, OLIVE, RUST, WHITE, MUSTARD, KHAKI, STONE, NAVY, SKY, CREAM, CHARCOAL, TEAL, WINE = (
    (0.78, 0.66, 0.48), (0.36, 0.4, 0.24), (0.7, 0.3, 0.17), (0.92, 0.92, 0.9), (0.85, 0.62, 0.18),
    (0.66, 0.57, 0.42), (0.6, 0.58, 0.54), (0.1, 0.14, 0.26), (0.55, 0.7, 0.88), (0.9, 0.85, 0.74),
    (0.2, 0.2, 0.22), (0.12, 0.42, 0.45), (0.45, 0.1, 0.16))
BROWN_HAIR, BLOND, BLACK_HAIR, AUBURN, GREY = mh.HAIR["brown"], mh.HAIR["blond"], mh.HAIR["black"], mh.HAIR["auburn"], mh.HAIR["grey"]
DARK_BROWN, LIGHT_BROWN, ASH_BLOND, WHITE_HAIR = mh.HAIR["dark_brown"], mh.HAIR["light_brown"], mh.HAIR["ash_blond"], mh.HAIR["white"]

CAST = {
    # ---- the Sahara crew: three men, two women
    "tunde": dict(gender="male", race="african", hair="short04", expression="smile",
                  clothes=["namuhekam_male_polo_shirt", "toigo_wool_pants", "toigo_ankle_boots_male"],
                  retint={"toigo_wool_pants": dict(whole=KHAKI)}),
    "jack": dict(gender="male", race="caucasian", hair="short03", expression="grin",
                 clothes=["elvs_male_shirt_untucked_bd1", "toigo_wool_pants", "culturalibre_male_boots"],
                 retint={"elvs_male_shirt_untucked_bd1": dict(whole=SKY), "toigo_wool_pants": dict(whole=STONE)},
                 tint={"short03": BROWN_HAIR}),
    "emeka": dict(gender="male", race="african", hair="afro01", expression="soft",
                  clothes=["elvs_male_boho_top1", "toigo_wool_pants", "culturalibre_sneakers"],
                  retint={"elvs_male_boho_top1": dict(whole=CREAM), "toigo_wool_pants": dict(whole=OLIVE)}),
    "amina": dict(gender="female", race="african", hair="elvs_reverse_french_braid_bun", expression="smile",
                  clothes=["mindfront_knitted_sweater_02", "toigo_harem_pants", "toigo_ballet_flats"],
                  retint={"mindfront_knitted_sweater_02": dict(whole=MUSTARD)}),
    "sophie": dict(gender="female", race="caucasian", hair="toigo_inverted_bob", expression="grin",
                   clothes=["punkduck_off-shoulder_long-sleeve_top", "toigo_wool_pants", "toigo_ankle_boots_female"],
                   retint={"toigo_wool_pants": dict(whole=SAND)}, tint={"toigo_inverted_bob": BLOND}),
    # ---- at the house and on the street (mostly white residents; varied ages and builds)
    "olivia": dict(gender="female", race="caucasian", age=0.22, hair="toigo_curled_under_bob", expression="smile",
                   skin="young_caucasian_female2", clothes=["toigo_female_suit_2", "mindfront_shoes_oxford_female"],
                   retint={"toigo_female_suit_2": dict(whole=CREAM)}, tint={"toigo_curled_under_bob": BLOND}),
    "daniel": dict(gender="male", race="caucasian", age=0.18, hair="culturalibre_hair_02", expression="soft",
                   height="max", skin="young_caucasian_male2", clothes=["toigo_male_suit_tie_and_jacket", "mindfront_shoes_oxford_male"],
                   tint={"culturalibre_hair_02": BROWN_HAIR}),
    "tom": dict(gender="male", race="caucasian", age=0.5, weight="max", hair="short02", expression="neutral",
                skin="middleage_caucasian_male", clothes=["male_worksuit01", "shoes04"], tint={"short02": GREY}),
    "emma": dict(gender="female", race="caucasian", age=0.02, hair="culturalibre_hair_01", expression="grin",
                 skin="young_caucasian_female", clothes=["toigo_camisole_top", "cortu_jeans_shorts", "dressupdoc_sandals1"],
                 tint={"culturalibre_hair_01": LIGHT_BROWN}),
    "claire": dict(gender="female", race="caucasian", age=0.12, hair="toigo_blunt_bob", expression="smile",
                   clothes=["punkduck_lace_up_blouse", "toigo_long_full_skirt", "toigo_ballet_flats"],
                   tint={"toigo_blunt_bob": AUBURN}),
    "mark": dict(gender="male", race="caucasian", age=0.35, weight="max", hair="elvs_grump_hair", expression="smile",
                 skin="middleage_caucasian_male", clothes=["namuhekam_male_polo_shirt", "toigo_wool_pants", "mindfront_shoes_oxford_male"],
                 retint={"toigo_wool_pants": dict(whole=NAVY)}, tint={"elvs_grump_hair": ASH_BLOND}),
    "lena": dict(gender="female", race="caucasian", age=0.3, hair="toigo_inverted_bob", expression="soft",
                 skin="middleage_caucasian_female", clothes=["mindfront_knitted_sweater_01", "toigo_wool_pants", "toigo_ankle_boots_female"],
                 retint={"toigo_wool_pants": dict(whole=CHARCOAL)}, tint={"toigo_inverted_bob": DARK_BROWN}),
    "guard": dict(gender="male", race="african", hair="short04", expression="neutral", muscle="max",
                  clothes=["elvs_male_shirt_tie_tucked1", "toigo_wool_pants", "mindfront_shoes_oxford_male"],
                  retint={"elvs_male_shirt_tie_tucked1": dict(whole=SKY), "toigo_wool_pants": dict(whole=NAVY)}),
    "kate": dict(gender="female", race="caucasian", age=0.15, hair="culturalibre_hair_01", expression="smile",
                 skin="young_caucasian_female2", clothes=["mindfront_knitted_sweater_02", "toigo_wool_pants", "toigo_ballet_flats"],
                 retint={"mindfront_knitted_sweater_02": dict(whole=CREAM), "toigo_wool_pants": dict(whole=STONE)},
                 tint={"culturalibre_hair_01": BLOND}),
    "ryan": dict(gender="male", race="caucasian", age=0.25, hair="culturalibre_hair_05", expression="grin",
                 skin="toigo_light_skin_male_freckles", clothes=["elvs_male_shirt_untucked_bd1", "toigo_wool_pants", "culturalibre_sneakers"],
                 retint={"elvs_male_shirt_untucked_bd1": dict(whole=WHITE), "toigo_wool_pants": dict(whole=NAVY)},
                 tint={"culturalibre_hair_05": AUBURN}),
    # ---- passers-by on the street
    "walker1": dict(gender="female", race="caucasian", age=0.1, hair="toigo_blunt_bob", expression="smile",
                    clothes=["punkduck_v_neck_top", "toigo_tiered_skirt", "toigo_ballet_flats"], tint={"toigo_blunt_bob": BLOND}),
    "walker2": dict(gender="male", race="african", age=0.15, hair="short02", expression="grin",
                    clothes=["elvs_male_shirt_untucked_bd1", "toigo_wool_pants", "culturalibre_sneakers"],
                    retint={"elvs_male_shirt_untucked_bd1": dict(whole=WHITE), "toigo_wool_pants": dict(whole=CHARCOAL)}),
    "walker3": dict(gender="male", race="caucasian", age=0.3, hair="culturalibre_hair_05", expression="soft",
                    skin="middleage_caucasian_male", clothes=["mindfront_knitted_sweater_01", "toigo_wool_pants", "mindfront_shoes_oxford_male"],
                    retint={"mindfront_knitted_sweater_01": dict(whole=TEAL), "toigo_wool_pants": dict(whole=KHAKI)},
                    tint={"culturalibre_hair_05": BROWN_HAIR}),
    "walker4": dict(gender="female", race="caucasian", age=0.05, hair="o4saken_long01", expression="smile",
                    clothes=["toigo_keyhole_tank_top", "toigo_skirt_with_lace_ruffle", "toigo_flats"],
                    tint={"o4saken_long01": BROWN_HAIR}),
    "walker5": dict(gender="female", race="caucasian", age=0.6, weight="max", hair="rehmanpolanski_hair_bun_brown", expression="soft",
                    skin="old_caucasian_female", clothes=["janexx_old_female_sweater", "toigo_long_full_skirt", "toigo_flats"],
                    tint={"rehmanpolanski_hair_bun_brown": WHITE_HAIR}),
    "walker6": dict(gender="male", race="caucasian", age=0.7, hair="short03", expression="smile",
                    skin="old_caucasian_male", clothes=["toigo_male_suit_tie_and_jacket", "mindfront_shoes_oxford_male"],
                    tint={"short03": GREY}),
}


def make(name, pose="stand", collection=None, obj_name=None, **over):
    spec = dict(CAST[name])
    rt = spec.pop("retint", {})
    tex = {a: mh.retint(a, name, **kw) for a, kw in rt.items()}
    spec.update(over)
    p = mh.POSES[pose] if isinstance(pose, str) else pose
    return mh.human(obj_name or name, pose=p, collection=collection, textures=tex, **spec)


def actor(name, collection=None, **over):
    """A live rig of a cast member, for animation (see mh.Actor)."""
    spec = dict(CAST[name])
    rt = spec.pop("retint", {})
    tex = {a: mh.retint(a, name, **kw) for a, kw in rt.items()}
    spec.update(over)
    return mh.Actor(name, collection=collection, textures=tex, **spec)
