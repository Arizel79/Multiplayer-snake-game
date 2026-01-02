import asyncio
import json
import logging
import random
import sys
from time import time

import websockets

from server.modules.config import *
from server.modules.config import DEAFAULT_SNAKE_COLORS, VALID_NAME_CHARS
from server.modules.config_obj import ServerConfig
from server.modules.dataclasses import *
from server.utils import get_random_id


class BaseMixin:
    def __init__(self, config: ServerConfig):
        self.config = config
        self.setup_logger(
            __name__, getattr(logging, self.config.logging_level), self.config.logging_file
        )
        self.logger.info(f"Logging level: {self.config.logging_level}")

        self.last_normal_snake_move_time = time()
        self.last_fast_snake_move_time = time()

        self.old_tick_time = time()

        self.logger.info(f"Admin password: {self.config.admin_password}")

        self._food_dict_cache = {}
        self._snake_dict_cache = {}
        self._last_cache_update = 0
        self.cache_ttl = 0.05

        self._send_cache_for_players = {}

        self.tps = 0
        self.tps_counter = 0

        self.last_tps_time = time()

        self.snakes = {}
        self.food = {}
        self.players = {}

        self.connections = {}

