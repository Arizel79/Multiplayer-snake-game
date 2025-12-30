import argparse
import asyncio
import logging
import random
import yaml
from server.modules.config import *

from server.modules.base import BaseServer

websockets_logger = logging.getLogger('websockets')
websockets_logger.setLevel(logging.CRITICAL)


class Server(BaseServer):
    pass


def positive_int(value):
    val = int(value)
    if val <= 0:
        raise argparse.ArgumentTypeError(f"{value} is not a positive integer")
    return val


def get_full_parser():
    parser = argparse.ArgumentParser(description="Multiplayer Snake game by @Arizel79 (server)")
    parser.add_argument('--config-file', type=str, help='Path to config file (YAML)')
    parser.add_argument('--host', type=str, help='Server host', default="0.0.0.0")
    parser.add_argument('--port', type=int, help='Server port', default=8090)
    parser.add_argument('--server_name', type=str, help='Server name', default="Snake Server")
    parser.add_argument('--server_desc', type=str, help='Description of server', default="This is server")
    parser.add_argument('--max_players', type=positive_int, help='Max online players count', default=20)
    parser.add_argument('--map_width', type=int, help='Width of server map', default=100)
    parser.add_argument('--map_height', type=int, help='Height of server map', default=100)
    parser.add_argument('--viewport_width', type=int, help='Width of players viewport', default=100)
    parser.add_argument('--viewport_height', type=int, help='Height of players viewport', default=100)
    parser.add_argument('--food_perc', type=int, help='Proportion food/map in perc', default=2)
    parser.add_argument('--default_move_timeout', type=float, help='Timeout move snake (sec)', default=0.1)
    parser.add_argument('--fast_move_timeout', type=float, help='Timeout move fast snake (sec)', default=0.07)
    parser.add_argument('--steal_chance', type=float, help='chance of stealing 1 percent of the body per tick',
                        default=0.003)
    parser.add_argument('--steal_chance_fast', type=float,
                        help='chance of stealing 1 segment of the body per tick, if snake is fast', default=0.01)
    parser.add_argument('--logging_level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Level of logging', default="INFO")
    return parser


async def run_server():
    parser = get_full_parser()
    args = parser.parse_args()

    if args.config_file:
        with open(args.config_file, 'r') as f:
            config = yaml.safe_load(f)

        game_state = Server(
            address=config.get('host', "0.0.0.0"),
            port=config.get('port', 8090),
            map_width=config.get('map_width', 100),
            map_height=config.get('map_height', 100),
            viewport_width=config.get('viewport_width', 100),
            viewport_height=config.get('viewport_height', 100),
            max_players=config.get('max_players', 20),
            server_name=config.get('server_name', "Snake Server"),
            server_desc=config.get('server_desc', "This is server"),
            logging_level=config.get('logging_level', "INFO"),
            max_food_perc=config.get('food_perc', 2),
            default_move_timeout=config.get('default_move_timeout', 0.1),
            fast_move_timeout=config.get('fast_move_timeout', 0.07),
            stealing_chanse_1percent=config.get('steal_chance', 0.003),
            fast_stealing_chance=config.get('steal_chance_fast', 0.01)
        )
    else:
        game_state = Server(
            address=args.host,
            port=args.port,
            map_width=args.map_width,
            map_height=args.map_height,
            viewport_width=args.viewport_width,
            viewport_height=args.viewport_height,
            max_players=args.max_players,
            server_name=args.server_name,
            server_desc=args.server_desc,
            logging_level=args.logging_level,
            max_food_perc=args.food_perc,
            default_move_timeout=args.default_move_timeout,
            fast_move_timeout=args.fast_move_timeout,
            stealing_chanse_1percent=args.steal_chance,
            fast_stealing_chance=args.steal_chance_fast
        )

    try:
        await game_state.run()
    except asyncio.CancelledError:
        pass
    finally:
        print("Server finished")


def main():
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt. Server quit")
        return


if __name__ == '__main__':
    raise Exception("DONT RUN THIS FILE< RUN MAIN>PY")