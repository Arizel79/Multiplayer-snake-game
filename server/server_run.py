import argparse
import asyncio
import logging
import sys

import yaml

from server.modules.base import BaseServer
from server.modules.config_obj import ServerConfig

websockets_logger = logging.getLogger("websockets")
websockets_logger.setLevel(logging.CRITICAL)


class Server(BaseServer):
    pass


def positive_int(value):
    val = int(value)
    if val <= 0:
        raise argparse.ArgumentTypeError(f"{value} is not a positive integer")
    return val


def get_full_parser():
    parser = argparse.ArgumentParser(
        description="Multiplayer Snake game by @Arizel79 (server)"
    )
    parser.add_argument(
        "--config-file",
        type=str,
        help="Path to config file (YAML)",
        default="config.yaml",
    )

    return parser


def load_yaml_config(config_file):
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)
    return config


def run_server():
    parser = get_full_parser()
    args = parser.parse_args()

    if args.config_file:
        config = load_yaml_config(args.config_file)

        config_server = config.get("server", {})
        config_game = config.get("game", {})
        config_map = config_game.get("game", {})
        config_viewport = config_game.get("viewport", {})
        config_snake = config_game.get("snake", {})
        config_logging = config.get("logging", {})

        config_default_mode = config_snake.get("default_mode", {})
        config_fast_mode = config_snake.get("fast_mode", {})
        config_obj = ServerConfig(
            address=config_server.get("host", "0.0.0.0"),
            port=config_server.get("port", 8090),
            map_width=config_map.get("width", 100),
            map_height=config_map.get("height", 100),
            viewport_width=config_viewport.get("width", 100),
            viewport_height=config_viewport.get("height", 100),
            max_players=config_server.get("max_players", 20),
            server_name=config_server.get("server_name", "Snake Server"),
            server_desc=config_server.get("server_desc", "This is server"),
            logging_level=config_logging.get("level", "INFO"),
            max_food_perc=config_map.get("food_perc", 2),
            default_move_timeout=config_default_mode.get("move_timeout", 0.1),
            default_stealing_chance=config_default_mode.get("steal_chance", 0.003),
            default_snake_length=config_snake.get("default_length", 0.003),
            fast_move_enable=config_fast_mode.get("enable", False),
            fast_move_timeout=config_fast_mode.get("move_timeout", 0.07),
            fast_stealing_chance=config_fast_mode.get("steal_chance", 0.01),
            admin_password=config_server.get("admin_password"),
        )

        server = Server(config=config_obj)

    else:
        raise ValueError("No config file specified")

    async def async_main(server):
        await server.run()

    asyncio.run(async_main(server))


def main():
    try:
        run_server()
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt. Server quit")
        return


if __name__ == "__main__":
    sys.exit("Don`t run this file, run main.py")
