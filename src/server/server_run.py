import argparse
import asyncio
import logging
import sys

import aiofiles
import yaml

from src.server.modules.base import Server
from src.server.modules.config_obj import ServerConfig

websockets_logger = logging.getLogger("websockets")
websockets_logger.setLevel(logging.CRITICAL)


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


def run_server():
    parser = get_full_parser()
    args = parser.parse_args()

    if args.config_file:

        server = Server(yaml_config_file=args.config_file)

    else:
        raise ValueError("No config file specified")

    async def async_main(server):
        await server.main()

    asyncio.run(async_main(server))


def main():
    try:
        run_server()
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt. Server quit")
        return


if __name__ == "__main__":
    sys.exit("Don`t run this file, run main.py")
