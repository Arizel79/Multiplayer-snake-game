import asyncio
from queue import Queue, Empty
import threading
import websockets
from socket import gaierror

import json
from sys import stdout
import traceback
import logging
from abc import ABC, abstractmethod
from colorama import init, Fore, Back, Style

class Disconnected(Exception):
    pass


class ServerConnectionError(Exception):
    pass


class ClientBase(ABC):
    MAX_SHOWN_MESSAGES_CHAT_OFF = 5
    MAX_SHOWN_MESSAGES_CHAT_ON = 32
    VERSION_NUMBER = "v0.1, client"

    def __init__(self, server_address=None, nickname=None, color=None, logging_level="debug"):
        self.version = self.VERSION_NUMBER

        self.show_debug = False
        self.server_address = server_address
        self.nickname = nickname
        self.color = color
        self.screen = None
        self.player_id = None
        self.player_color = "green"
        self.game_state = None
        self.last_key = None
        self.running = True
        self.chat_messages = []
        self.max_chat_messages = 10
        self.is_open_chat = False
        self.chat_prompt = ""
        self.direction = None

        self.to_send = Queue()
        self.new_direction = None
        self.is_open_tablist = False
        self.is_open_help = False
        self.server_desc = "Welcome to server!"

        self.state = None

        self.alert_message = None
        self.input_queue = Queue()  # Очередь для хранения нажатых клавиш
        self.input_thread_running = True
        self.input_thread = threading.Thread(target=self.input_output_thread_worker, daemon=True)

        self.logging_level = logging_level.upper()
        self.setup_logger(__name__, "server.log", self.logging_level)

    def setup_logger(self, name, log_file='client.log', level=logging.INFO):
        """Настройка логгера"""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_formatter = logging.Formatter('[%(levelname)s] %(message)s')

        # To file
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(file_formatter)

        # To console
        console_handler = logging.StreamHandler(stdout)
        console_handler.setFormatter(console_formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        return self.logger

    @abstractmethod
    def input_output_thread_worker(self):
        """Ввод-вывод"""
        pass

    @abstractmethod
    async def handle_input(self):
        """Обработка ввода (очередь self.input_queue)"""
        pass

    def get_game_map_coords_on_scr(self):
        x, y = self.screen.get_sizes()
        x1, y1, x2, y2 = 1, 1, x - 2, y - 2
        return x1, y1, x2, y2

    @abstractmethod
    def handle_chat_message(self, message):
        """Обрабатываем полученое сообщение"""

    async def on_my_death(self, data):

        self.state = "died"
        self.is_open_chat = False
        self.chat_prompt = ""

        self.direction = None
        self.alert_message = data.get("data", "no died message recived")

    async def handle_data(self, data):
        # self.logger.debug(f"Recieved data: {data}")
        if data.get("type", None) == "game_state":
            self.game_state = data

        elif data.get("type", None) == "set_server_desc":
            self.server_desc = data["data"]

        elif data.get("type", None) == "chat_message":
            self.handle_chat_message(data)

        elif data.get("type", None) == 'connection_error':
            raise ServerConnectionError(data["data"])

        elif data.get("type", None) == "you_died":
            await self.on_my_death(data)
        else:
            assert False, data

    def is_message_for_send(self, messsage):
        if messsage in [".clear", ".cl", ".q", ".quit"]:
            return False

        return True

    def quit(self):
        self.logger.debug("(in self.quit) Quiting...")
        print("Quit.")
        self.state = None
        self.running = False
        self.input_thread_running = False

    async def send_chat(self):
        message = self.chat_prompt.lstrip()
        if message != "":
            if message.startswith("."):
                ls = message.split()
                if ls[0] in [".clear", ".cl"]:
                    self.chat_messages = []
                    return
                elif ls[0] in [".q", ".quit"]:
                    self.logger.info("User-side quit...")
                    self.quit()
                    return
            if self.is_message_for_send(message):
                self.to_send.put({"type": "chat_message", "data": message})

            else:
                if message == "/kill":
                    await self.websocket.send(json.dumps({"type": 'kill_me'}))
                self.chat_messages.append(self.chat_prompt)

            self.chat_prompt = ""
            self.is_open_chat = False

    def add_chat_message(self, message):
        self.chat_messages.append(message)

    def is_me_alive(self):
        if self.game_state is None:
            return False
        snake = self.game_state["snakes"].get(self.player_id, None)
        if snake is None:
            return False

        return bool(self.game_state) and snake["alive"]

    async def connect(self, uri):
        async with websockets.connect(uri, ping_timeout=3, open_timeout=8) as websocket:
            self.logger.info(f"Connected to {self.server_address}")
            self.state = "game"
            self.websocket = websocket
            await websocket.send(json.dumps({
                'name': self.nickname,
                'color': self.color
            }))

            message = await asyncio.wait_for(websocket.recv(), timeout=0.1)
            data = json.loads(message)
            if data["type"] == "connection_error":
                raise ConnectionError(data["data"])
            self.player_id = data["player_id"]

            while self.running:
                if self.is_me_alive() and self.state == "died":
                    self.state = "game"

                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                    data = json.loads(message)
                    await self.handle_data(data)
                except asyncio.TimeoutError:
                    pass

                await self.handle_input()

                while not self.to_send.empty():
                    await websocket.send(json.dumps(self.to_send.get()))

    def get_follow(self) -> (int, int):
        try:
            return [i for i in self.game_state["snakes"][str(self.player_id)]["body"][0].values()]
        except (KeyError, TypeError):
            return 0, 0

    def get_my_coords(self) -> (int, int):
        return self.get_follow()

    def calc_coords(self, mx, my) -> (int, int):
        px, py = self.get_my_coords()
        sx1, sy1, sx2, sy2 = self.get_game_map_coords_on_scr()
        cX, cY = (sx1 + sx2) // 2, (sy1 + sy2) // 2
        return cX + sx1 - px + mx, cY + sy1 - py + my

    @abstractmethod
    def render(self):
        """Отрисовка"""
        pass

    def alert(self, title, message):
        self.state = "alert"
        self.alert_message = f"<bold>{title}</bold>\n\n{message}"

    @abstractmethod
    async def wait_for_end(self):
        """Бесконечно ожидаем, пока программа не завершится (self.state == None)"""

    async def run_game(self):
        print(f"{Fore.LIGHTBLACK_EX}* {Fore.LIGHTYELLOW_EX}Welcome to Multiplayer Snake {self.version}")
        print(f"{Fore.LIGHTBLACK_EX}* Powered by Arizel79 (https://github.com/Arizel79)")
        print(f"* Source: https://github.com/Arizel79/Multiplayer-snake-game{Style.RESET_ALL}")
        print(f"Server: {self.server_address}; name: {self.nickname}; color: {self.color}")
        print("")
        self.logger.info(f"Logging level: {self.logging_level}")
        try:
            self.input_thread.start()
            try:
                self.logger.info(f"Trying connecting to {self.server_address}...")
                self.alert(f"Connecting to {self.server_address}", "<b>Please, wait...<b/>")
                await self.connect(f"ws://{self.server_address}")


            except websockets.exceptions.ConnectionClosedOK:
                self.alert("<red>Disconnected</red>", "<b>Server closed</b>\n\nYou can try reconnect later")
                await self.wait_for_end()


            except (OSError, gaierror, ConnectionRefusedError) as e:
                self.logger.error(f"{type(e).__name__}: {e}")
                self.alert(f"<red>Error connecting to {self.server_address}</red>",
                           f"<b>{type(e).__name__}</b>\n\n{e}")
                await self.wait_for_end()

            except ConnectionError as e:
                self.logger.warning(f"{type(e).__name__}: {e}")
                self.alert("<red>Server send error</red>", e)
                await self.wait_for_end()

            except Exception as e:
                if type(e) == KeyboardInterrupt:
                    raise KeyboardInterrupt
                traceback_str = traceback.format_exc()
                self.logger.critical(traceback_str)
                self.logger.critical(f"Game crashed. Error: {type(e).__name__}: {e}")


        except KeyboardInterrupt:
            self.logger.warning("KeyboardInterrupt received, shutting down...")
        finally:


            self.running = False
            self.input_thread_running = False

            if hasattr(self, 'input_thread') and self.input_thread.is_alive():
                self.input_thread.join(timeout=0.5)
