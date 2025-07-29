import argparse
from client_cli import *
from client_gui import *

async def run_client():
    parser = argparse.ArgumentParser(description="Multiplayer Snake game CLI/GUI edition")
    parser.add_argument('--mode', "-m", type=str, choices=['cli', "gui"],
                        help='Game mode', default="cli")
    parser.add_argument('--name', "--n", type=str, help='Snake name', default=f"player_{randint(0, 99999)}")
    parser.add_argument('--color', "--c", type=str, help='Snake color', default=choice(ClientCLI.SNAKE_COLORS))
    parser.add_argument('--server', "--s", type=str, help='Server address', default="localhost:8090")
    parser.add_argument('--log_lvl', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Level of logging', default="INFO")

    parser.add_argument("--interactive", "--i", action="store_true", help = "Enable interactive prompting (default: False)")
    args = parser.parse_args()
    if args.mode == "cli":
        g = ClientCLI(args.server, args.name, args.color, logging_level=args.log_lvl, interactive=args.interactive)
    elif args.mode == "gui":
        g = ClientGUI(args.server, args.name, args.color, logging_level=args.log_lvl, interactive=args.interactive)
    await g.run_game()
    # await run_game(args.address, args.name, args.skin)


def main():
    try:
        asyncio.run(run_client())
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
