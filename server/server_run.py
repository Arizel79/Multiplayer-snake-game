import argparse
import asyncio
import logging
import random

from server.modules.base import BaseServer

websockets_logger = logging.getLogger('websockets')
websockets_logger.setLevel(logging.CRITICAL)  # Уменьшите уровень логирования если нужно


class Server(BaseServer):
    pass


def positive_int(value):
    val = int(value)
    if val <= 0:
        raise argparse.ArgumentTypeError(f"{value} is not a positive integer")
    return val


async def run_server():
    parser = argparse.ArgumentParser(description="Multiplayer Snake game by @Arizel79 (server)")
    parser.add_argument('--host', type=str,
                        help='Server host (default: 0.0.0.0)', default="0.0.0.0")
    parser.add_argument('--port', "--p", type=int,
                        help='Server port (default: 8090)', default=8090)
    parser.add_argument('--server_name', type=str,
                        help='Server name', default="Snake Server")
    parser.add_argument('--server_desc', type=str,
                        help='Description of server', default="This is server")
    parser.add_argument('--max_players', type=positive_int,
                        help='Max online players count', default=20)
    parser.add_argument('--map_width', "--width", "--w", "--x_size", type=int,
                        help='Width of server map', default=100)
    parser.add_argument('--map_height', "--height", "--h", "--y_size", type=int,
                        help='Height of server map',
                        default=100)
    parser.add_argument('--food_perc', type=int, help='Proportion food/map in perc', default=2)
    parser.add_argument('--default_move_timeout', '--default_move', type=float,
                        help='Timeout move snake (sec)',
                        default=0.1)
    parser.add_argument('--fast_move_timeout', '--fast_move', type=float,
                        help='Timeout move fast snake (sec)',
                        default=0.07)

    parser.add_argument('--steal_chance', type=float,
                        help='chance of stealing 1 percent of the body per tick',
                        default=0.003)
    parser.add_argument('--steal_chance_fast', type=float,
                        help='chance of stealing 1 segment of the body per tick, if snake is fast',
                        default=0.01)
    parser.add_argument('--logging_level', '--log_lvl', type=str,
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Level of logging', default="INFO")
    args = parser.parse_args()

    game_state = Server(address=args.host, port=args.port, map_width=args.map_width, map_height=args.map_height,
                        max_players=args.max_players, server_name=args.server_name, server_desc=args.server_desc,
                        logging_level=args.logging_level, max_food_perc=args.food_perc,
                        default_move_timeout=args.default_move_timeout, fast_move_timeout=args.fast_move_timeout,
                        stealing_chanse_1percent=args.steal_chance, fast_stealing_chance=args.steal_chance_fast)
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