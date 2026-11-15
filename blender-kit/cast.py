"""The recurring cast: three men and two women, with fixed looks."""
import mh

SAND, OLIVE, RUST, WHITE, MUSTARD, KHAKI, STONE, BLACK = (
    (0.78, 0.66, 0.48), (0.33, 0.37, 0.22), (0.62, 0.25, 0.14), (0.9, 0.9, 0.88), (0.8, 0.58, 0.16),
    (0.6, 0.52, 0.38), (0.55, 0.53, 0.5), (0.06, 0.06, 0.07))

CAST = {
    # the driver: field jacket, jeans, boots
    "tunde": dict(gender="male", race="african", clothes=["male_casualsuit05", "shoes04"], hair="short04",
                  muscle="average"),
    # front passenger: rust tee, khaki trousers
    "amina": dict(gender="female", race="african", clothes=["female_casualsuit01", "shoes03"], hair="bob01",
                  retint={"female_casualsuit01": dict(top=RUST, bottom=KHAKI)}),
    # back seat: white tee + jeans, fedora
    "chidi": dict(gender="male", race="african", clothes=["male_casualsuit06", "shoes01", "fedora01"], hair=None,
                  retint={"male_casualsuit06": dict(top=WHITE)}),
    # back seat: mustard tee, denim shorts
    "zainab": dict(gender="female", race="african", clothes=["female_casualsuit02", "shoes05"], hair="braid01",
                   retint={"female_casualsuit02": dict(top=MUSTARD)}),
    # back seat: olive tee, stone trousers
    "emeka": dict(gender="male", race="african", clothes=["male_casualsuit04", "shoes06"], hair="short01",
                  weight="average", retint={"male_casualsuit04": dict(top=OLIVE, bottom=STONE)}),
    # extras for the house scene
    "ngozi": dict(gender="female", race="african", clothes=["female_elegantsuit01", "shoes03"], hair="long01"),
    "bayo": dict(gender="male", race="african", clothes=["male_casualsuit01", "shoes01"], hair="short03"),
    "kunle": dict(gender="male", race="african", clothes=["male_worksuit01", "shoes04"], hair="short01"),
    "guard": dict(gender="male", race="african", clothes=["male_elegantsuit01", "shoes01"], hair="short04"),
}


def make(name, pose="stand", collection=None, obj_name=None, **over):
    spec = dict(CAST[name])
    rt = spec.pop("retint", {})
    tex = {a: mh.retint(a, name, **kw) for a, kw in rt.items()}
    spec.update(over)
    p = mh.POSES[pose] if isinstance(pose, str) else pose
    return mh.human(obj_name or name, pose=p, collection=collection, textures=tex, **spec)
