import asyncio
import json
import logging
import random
import sys
from time import time

import websockets

from server.modules.config import *
from server.modules.config import DEAFAULT_SNAKE_COLORS, VALID_NAME_CHARS
from server.modules.dataclasses import *
from server.utils import get_random_id


class BaseMixin:
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
        fast_move_timeout=0.1,
        stealing_chanse_1percent=0.003,
        fast_stealing_chance=0.5,
        viewport_width=BASE_VIEWPORT_WIDTH,
        viewport_height=BASE_VIEWPORT_HEIGHT,
        admin_password=None,
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

        self.snakes = {}
        self.food = {}
        self.players = {}
        self.max_players = max_players
        self.connections = {}

        if server_desc is None:
            self.server_desc = f"<green>Welcome to our Server {server_name}!</green>"
        else:
            self.server_desc = server_desc

        self.game_speed = 0.001
        self.max_food_relative = max_food_perc / 100
        self.max_food = (self.width * self.height) * self.max_food_relative

        self.min_stealing_snake_size = DEFAULT_SNAKE_LENGHT + 1
        self.stealing_chance = stealing_chanse_1percent
        self.steal_percentage = 0.01

        self.fast_stealing_chance = fast_stealing_chance
        self.fast_steal_abs_size = 1

        self.old_tick_time = time()
        self.tick = 0.02

        self.last_normal_snake_move_time = time()
        self.last_fast_snake_move_time = time()

        self.logging_level = logging_level
        self.setup_logger(__name__, getattr(logging, self.logging_level), "server.log")
        self.logger.info(f"Logging level: {self.logging_level}")

        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.viewport_scale_factor = 1

        self.admin_password = admin_password
        self.logger.info(f"Admin password: {self.admin_password}")

        self.spatial_grid = {}
        self.grid_cell_size = 1

        # TPS tracking
        self.tps_counter = 0
        self.last_tps_time = time()
        self.tps = 0
        self.tps_log_interval = 5

        self._food_dict_cache = {}
        self._snake_dict_cache = {}
        self._last_cache_update = 0
        self.cache_ttl = 0.05

        self._send_cache_for_players = {}
