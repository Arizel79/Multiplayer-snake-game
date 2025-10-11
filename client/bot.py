import asyncio
import os
import random

from client_base import *
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
        while self.state != None:
            await asyncio.sleep(0.01)

        self.logger.debug("Wait_for_quit finished")


LOGS_DIR = "bot_logs"
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)


async def run_bot(server, bot_name, bot_color):
    bot = Bot(
        server=server,
        nickname=bot_name,
        color=bot_color,
        logs_file=f"bot_logs/{bot_name}.log",
        logging_level="DEBUG",
        logging_name=f"{bot_name}",
    )
    try:
        bot.logger.info(f"Bot {bot_name} created")
        await bot.run_game()
    finally:
        bot.logger.info(f"Bot {bot_name} finished")


async def main():
    num_bots = 200
    SERVER = "localhost:8090"

    tasks = []
    for i in range(num_bots):
        tasks.append(
            asyncio.create_task(
                run_bot(
                    server=SERVER,
                    bot_name=f"BOT_{str(i)}_{random.randint(0, 100_000)}",
                    bot_color="red;green,lime",
                )
            )
        )

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
