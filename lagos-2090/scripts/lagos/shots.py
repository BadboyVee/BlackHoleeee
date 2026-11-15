"""Shot table: credits + finishing parameters (pure Python; used by scripts/post.py).
Shot-local frames are 1..90; global frame = (shot-1)*90 + local."""

NAME = "VEEE"

SHOTS = {
    1: {"name": "hover-danfo under the overpass",
        "credit": {"lines": ["CREATED BY", NAME]},
        "post": {}},
    2: {"name": "rooftop garden",
        "credit": {"lines": ["CONCEPT AND DESIGN", NAME]},
        "post": {}},
    3: {"name": "market street", "post": {}},
    4: {"name": "electric okada by the red kiosk",
        "credit": {"lines": ["3D ANIMATION", NAME]},
        "post": {}},
    5: {"name": "Third Mainland Bridge at sunset", "post": {}},
    6: {"name": "roadside corner", "post": {}},
    7: {"name": "inside the danfo",
        "credit": {"lines": ["STORYLINE", NAME]},
        "post": {}},
    8: {"name": "lagoon-side park from above",
        "title_card": {"start": 66, "text": "LAGOS 2090", "sub": ("BY " + NAME, 24, 0.7)},
        "post": {}},
}
for _s in SHOTS.values():
    if "credit" in _s:
        _s["credit"].update(size=19, size2=36, tracking=0.55)
