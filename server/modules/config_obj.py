from time import time

from server.modules.config import *
from server.modules.config import DEAFAULT_SNAKE_COLORS, VALID_NAME_CHARS
from server.modules.dataclasses import *


class ServerConfig:
    def __init__(
        self,
        address,
        port,
        map_width=80,
        map_height=80,
        max_players=20,
        server_name="Server",
        server_desc=None,
        logging_level="debug",
        max_food_perc=10,
        default_move_timeout=0.3,
        fast_move_enable=False,
        fast_move_timeout=0.1,
        default_snake_length=1,
        default_stealing_chance=0.003,
        fast_stealing_chance=0.5,
        viewport_width=BASE_VIEWPORT_WIDTH,
        viewport_height=BASE_VIEWPORT_HEIGHT,
        admin_password=None,
            enable_chat=True,
            max_chat_message_length=100
    ):

        self.port = port
        self.address = address

        self.width = map_width
        self.height = map_height

        self.snake_colors = DEAFAULT_SNAKE_COLORS

        self.DEFAULT_MOVE_TIMEOUT = default_move_timeout
        self.FAST_MOVE_TIMEOUT = fast_move_timeout
        self.MIN_LENGHT_FAST_ON = MIN_LENGHT_FAST_ON

        self.VALID_NAME_CHARS = VALID_NAME_CHARS

        self.max_players = max_players

        if server_desc is None:
            self.server_desc = f"<green>Welcome to our Server {server_name}!</green>"
        else:
            self.server_desc = server_desc

        self.game_speed = 0.001
        self.max_food_relative = max_food_perc / 100
        self.max_food = (self.width * self.height) * self.max_food_relative

        self.min_stealing_snake_size = 1
        self.stealing_chance = default_stealing_chance
        self.steal_percentage = 0.01

        self.fast_move_enable = fast_move_enable
        self.fast_stealing_chance = fast_stealing_chance
        self.fast_steal_abs_size = 1

        self.default_snake_length = default_snake_length

        self.tick = 0.02

        self.logging_level = logging_level.upper()

        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.viewport_scale_factor = 1

        self.admin_password = admin_password

        self.spatial_grid = {}
        self.grid_cell_size = 1

        # TPS tracking

        self.tps_log_interval = 5

        self.enable_chat = enable_chat
        self.max_chat_message_length = max_chat_message_length
