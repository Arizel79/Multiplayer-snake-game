import asyncio
import os
import random
import argparse
from src.client.client_base import *
from random import randint


class Bot(ClientBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.run_mode = "bot"

    def handle_chat_message(self, message):
        pass

    async def handle_input(self):
        pass

    def input_output_thread_worker(self):
        pass

    def quit_session(self):
        self.is_game_session_now = False

    def render(self):
        pass

    async def wait_for_end_session(self):
        while self.is_game_session_now and self.running:
            await asyncio.sleep(0.01)
        self.logger.debug("wait_for_end_session finished")

    async def wait_for_quit(self):
        while self.state is not None:
            await asyncio.sleep(0.01)
        self.logger.debug("Wait_for_quit finished")


def get_color(colors_list):
    return f"{random.choice(colors_list)};{random.choice(colors_list)}"


async def run_bot(server, bot_name, bot_color, logs_file, log_level):
    bot = Bot(
        server=server,
        nickname=bot_name,
        color=bot_color,
        logs_file=logs_file,
        logging_level=log_level,
        logging_name=f"{bot_name}",
    )
    try:
        bot.logger.info(f"Bot {bot_name} created")
        await bot.run_game()
    finally:
        bot.logger.info(f"Bot {bot_name} finished")


def parse_args():
    parser = argparse.ArgumentParser(description="Launch multiple bots for game server")
    parser.add_argument("-n", "--num-bots", type=int, default=1,
                        help="Number of bots (default: 1)")
    parser.add_argument("-s", "--server", type=str, required=True, 
                        help="Server address in format host:port")
    parser.add_argument("--enable-logs", action="store_true",
                        help="Enable logging to files (default: disabled)")
    parser.add_argument("--log-dir", type=str, default="bot_logs",
                        help="Directory to store log files (default: bot_logs)")
    parser.add_argument("--log-level", type=str, default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Logging level (default: INFO)")
    parser.add_argument("--bot-prefix", type=str, default="bot_",
                        help="Bot name prefix (default: bot_)")
    parser.add_argument("--colors", type=str, default="red,green,yellow,cyan,blue",
                        help="Comma-separated list of available colors (default: red,green,yellow,cyan,blue)")
    return parser.parse_args()


async def async_main(args):
    if args.enable_logs:
        if not os.path.exists(args.log_dir):
            os.makedirs(args.log_dir)
        logs_file_for_bot = lambda name: os.path.join(args.log_dir, f"{name}.log")
    else:
        logs_file_for_bot = lambda name: None

    colors_list = [c.strip() for c in args.colors.split(",")]

    tasks = []
    for i in range(args.num_bots):
        random_suffix = "".join(random.choices("0123456789abcdef", k=12))
        bot_name = f"{args.bot_prefix}{random_suffix}"
        bot_color = get_color(colors_list)
        logs_file = logs_file_for_bot(bot_name)

        tasks.append(
            asyncio.create_task(
                run_bot(
                    server=args.server,
                    bot_name=bot_name,
                    bot_color=bot_color,
                    logs_file=logs_file,
                    log_level=args.log_level,
                )
            )
        )

    await asyncio.gather(*tasks)


def main():
    args = parse_args()
    asyncio.run(async_main(args))


if __name__ == "__main__":
    main()
