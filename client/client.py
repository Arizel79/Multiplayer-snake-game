import json
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import argparse
from client_cli import ClientCLI
from client_gui import ClientGUI
import asyncio
from random import randint, choice
import json

GAME_CONFIG_FILENAME = "client/.game_config.json"

async def run_client():
    parser = argparse.ArgumentParser(description="Multiplayer Snake game CLI/GUI edition")
    with open(GAME_CONFIG_FILENAME, "w+") as f:
        try:
            game_config = json.load(f)
        except json.decoder.JSONDecodeError as e:
            pass


    parser.add_argument('--mode', "-m", type=str, choices=['cli', "gui"],
                        help='Game mode', default="cli")
    parser.add_argument('--name', "--n", type=str, help='Snake name', default=f"player_{randint(0, 99999)}")
    parser.add_argument('--color', "--c", type=str, help='Snake color', default=choice(ClientCLI.SNAKE_COLORS))
    parser.add_argument('--server', "--s", type=str, help='Server address', default="localhost:8090")
    parser.add_argument('--log_lvl', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Level of logging', default="INFO")

    parser.add_argument("--use_main_menu", "--menu", default=False, action="store_true", help = "Enable interactive main menu (default: False)")
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
