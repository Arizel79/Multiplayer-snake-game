import json
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import argparse
from client_cli import ClientCLI
from client_gui import ClientGUI
import asyncio
from random import randint, choice
import json
import logging
from sys import stdout
from pathlib import Path

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console_formatter = logging.Formatter('[%(levelname)s] - %(name)s - %(message)s')

console_handler = logging.StreamHandler(stdout)
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)


DEFAULT_CONFIG = {"run_mode": "gui",
                  "use_main_menu": True,
                  "server": "localhost:8090",
                  "player": f"player_{randint(0, 99999)}",
                  "color": choice(ClientCLI.SNAKE_COLORS),
                  }
GAME_CONFIG_FILENAME = "client\game_config.json"

async def run_client():
    parser = argparse.ArgumentParser(description="Multiplayer Snake game CLI/GUI edition")
    # Проверяем, существует ли файл
    if not Path(GAME_CONFIG_FILENAME).exists():
        logger.warning("Config file not found. Creating with defaults.")
        with open(GAME_CONFIG_FILENAME, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        game_config = DEFAULT_CONFIG
    else:
        # Читаем файл (режим "r", а не "w+")
        with open(GAME_CONFIG_FILENAME, "r", encoding="utf-8") as f:
            try:
                game_config = json.load(f)
                logger.debug(f"Read game config: {game_config}")
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON in config: {e}. Resetting to defaults.")
                game_config = DEFAULT_CONFIG
                # Перезаписываем файл с дефолтными значениями
                with open(GAME_CONFIG_FILENAME, "w", encoding="utf-8") as f:
                    json.dump(DEFAULT_CONFIG, f, indent=4)


    parser.add_argument('--mode', "--m", type=str, choices=['cli', "gui"],
                        help='Game mode (cli/gui)', default=game_config["run_mode"])
    parser.add_argument('--name', "--n", type=str, help='Snake name', default=game_config["player"])
    parser.add_argument('--color', "--c", type=str, help='Snake color', default=game_config["color"])
    parser.add_argument('--server', "--s", type=str, help='Server address', default=game_config["server"])
    parser.add_argument('--log_lvl', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Level of logging', default="INFO")

    parser.add_argument("--use_main_menu", "--menu", default=game_config["use_main_menu"], action="store_true", help = "Enable interactive main menu (default: False)")
    args = parser.parse_args()
    if args.mode == "cli":
        g = ClientCLI(GAME_CONFIG_FILENAME,args.server, args.name, args.color, use_main_menu=args.use_main_menu, logging_level=args.log_lvl)
    elif args.mode == "gui":
        g = ClientGUI(GAME_CONFIG_FILENAME,args.server, args.name, args.color, use_main_menu=args.use_main_menu, logging_level=args.log_lvl)
    else:
        raise ValueError("argument mode must be cli/gui")
    await g.run_game()
    # await run_game(args.address, args.name, args.skin)


def main():
    try:
        asyncio.run(run_client())
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
