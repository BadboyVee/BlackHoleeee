"""SPARKS, a fan concept: the film. All on white, to black at the very end."""
from engine.render import Film
from . import scenes
from .score import DURATION, SIZE, T_BLACK


class Sparks(Film):
    duration = DURATION
    size = SIZE

    def __init__(self):
        scenes.preload()                                 # load the sprites before the render forks

    def bg(self, t):
        return (0.0, 0.0, 0.0) if t >= T_BLACK else (1.0, 1.0, 1.0)

    def draw(self, c, t):
        scenes.draw(c, t)

    def mb(self, t):
        return 8

    def shutter(self, t):
        return 0.5

    def fx(self, t):
        return {"grain": 0.0, "vignette": 0.0}
