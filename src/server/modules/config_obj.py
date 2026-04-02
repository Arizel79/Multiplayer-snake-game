from time import time

import aiofiles
import yaml

from src.server.modules.config import *
from src.server.modules.config import DEAFAULT_SNAKE_COLORS, VALID_NAME_CHARS
from src.server.modules.dataclasses import *


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
        logging_console_level="debug",
        logging_file=None,
            logging_file_level="debug",
        max_food_perc=10,
        default_move_timeout=0.3,
        fast_move_enable=False,
        fast_move_timeout=0.1,
        default_snake_length=1,
        default_stealing_chance=0.003,
        fast_stealing_chance=0.5,
        viewport_width=BASE_VIEWPORT_WIDTH,
        viewport_height=BASE_VIEWPORT_HEIGHT,
        all_players_admins=False,
        admin_password=None,
        enable_chat=True,
        max_chat_message_length=100,
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

        self.tps_limit = 20
        self.game_speed = 1 / self.tps_limit
        self.max_food_relative = max_food_perc / 100
        self.max_food = (self.width * self.height) * self.max_food_relative

        self.min_stealing_snake_size = 1
        self.stealing_chance = default_stealing_chance
        self.steal_percentage = 0.01

        self.fast_move_enable = fast_move_enable
        self.fast_stealing_chance = fast_stealing_chance
        self.fast_steal_abs_size = 1

        self.default_snake_length = default_snake_length


        # logging
        self.logging_console_level = logging_console_level.upper()
        self.logging_file = logging_file
        if not self.logging_file:
            self.logging_file = None
        self.logging_file_level = logging_file_level.upper()

        # viewport
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.viewport_scale_factor = 1

        self.all_players_admins = all_players_admins
        self.admin_password = admin_password

        self.spatial_grid = {}
        self.grid_cell_size = 1

        # TPS tracking
        self.tick = 1 / self.tps_limit

        self.tps_log_interval = 5

        self.enable_chat = enable_chat
        self.max_chat_message_length = max_chat_message_length

    @staticmethod
    def from_yaml(dict_):
        config = dict_
        config_server = config.get("server", {})
        config_admin = config_server.get("admin", {})
        config_chat = config_server.get("chat", {})
        config_game = config.get("game", {})
        config_map = config_game.get("map", {})
        config_viewport = config_game.get("viewport", {})
        config_snake = config_game.get("snake", {})
        config_logging = config.get("logging", {})

        config_default_mode = config_snake.get("default_mode", {})
        config_fast_mode = config_snake.get("fast_mode", {})
        config_obj = ServerConfig(
            address=config_server.get("host", "0.0.0.0"),
            port=config_server.get("port", 8090),

            server_name=config_server.get("name", "Snake Server"),
            server_desc=config_server.get("description", "This is server"),
            max_players=config_server.get("max_players", 20),

            logging_console_level=config_logging.get("console_level", "INFO"),
            logging_file=config_logging.get("file"),
            logging_file_level=config_logging.get("file_level", "INFO"),

            map_width=config_map.get("width", 100),
            map_height=config_map.get("height", 100),
            viewport_width=config_viewport.get("width", 100),
            viewport_height=config_viewport.get("height", 100),

            max_food_perc=config_map.get("food_perc", 2),
            default_snake_length=config_snake.get("default_length", 0.003),

            default_move_timeout=config_default_mode.get("move_timeout", 0.1),
            default_stealing_chance=config_default_mode.get("steal_chance", 0.003),
            fast_move_enable=config_fast_mode.get("enable", False),
            fast_move_timeout=config_fast_mode.get("move_timeout", 0.07),
            fast_stealing_chance=config_fast_mode.get("steal_chance", 0.01),

            all_players_admins=config_admin.get("all_players_admins"),
            admin_password=config_admin.get("admin_password"),
            enable_chat=config_chat.get("enable", True),
            max_chat_message_length=config_chat.get("max_message_length", True),
        )
        return config_obj

    @staticmethod
    async def load_yaml_config(config_file):
        async with aiofiles.open(config_file, mode="r") as f:
            content = await f.read()
            config = yaml.safe_load(content)
        return config

    @staticmethod
    async def get_config_obj_from_file(yaml_config_file):
        dict_ = await ServerConfig.load_yaml_config(yaml_config_file)
        return ServerConfig.from_yaml(dict_)
