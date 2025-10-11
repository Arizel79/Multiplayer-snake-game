from string import ascii_letters, digits

DEFAULT_FOOD_TYPE = 1
DEFAULT_FOOD_COLOR = "orange"
DEFAULT_FOOD_SIZE = 1

VALID_NAME_CHARS = ascii_letters + digits + "_"
DEFAULT_SNAKE_LENGHT = 2
DIRECTIONS = ["right", "down", "left", "up"]

DEAFAULT_SNAKE_COLORS = [
    "red",
    "green",
    "lime",
    "blue",
    "yellow",
    "magenta",
    "cyan",
    "white",
    "orange",
    "violet",
    "turquoise",
    "light_blue",
]

BASE_VIEWPORT_WIDTH = 70
BASE_VIEWPORT_HEIGHT = 50

MIN_LENGHT_FAST_ON = 4

MAX_PLAYER_COLOR_LENGHT = 16

class FOOD_TYPES:
    default = 0
    death = 1
    from_fast_snake = 2
