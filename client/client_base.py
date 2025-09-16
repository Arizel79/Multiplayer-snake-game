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

    def __init__(self, game_config_filename=None, server=None, nickname=None, color=None, use_main_menu=False, logging_level="debug", logs_file="client/client.log", logging_name="client"):
        self.version = self.VERSION_NUMBER
        self.run_mode = "base"
        self.ascii_logo = """  █████████                       █████              
 ███░░░░░███                     ░░███               
░███    ░░░  ████████    ██████   ░███ █████  ██████ 
░░█████████ ░░███░░███  ░░░░░███  ░███░░███  ███░░███
 ░░░░░░░░███ ░███ ░███   ███████  ░██████░  ░███████ 
 ███    ░███ ░███ ░███  ███░░███  ░███░░███ ░███░░░  
░░█████████  ████ █████░░████████ ████ █████░░██████ 
 ░░░░░░░░░  ░░░░ ░░░░░  ░░░░░░░░ ░░░░ ░░░░░  ░░░░░░ 
"""

        if not logging_level is None:
            self.logging_level = logging_level.upper()
        else:
            self.logging_level = None

        self.logs_file = logs_file
        self.logging_name = logging_name
        self.setup_logger(self.logging_name, self.logs_file, self.logging_level)

        self.use_main_menu = use_main_menu

        if self.use_main_menu:
            self.state = "main_menu"
        else:
            self.state = None

        self.show_debug = False
        self.server = server
        self.player_name = nickname
        self.color = color
        self.screen = None
        self.player_id = None
        self.player_color = "green"
        self.game_state = None
        self.last_key = None

        self.running = True
        self.is_game_session_now = False
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


        self.game_config_filename = game_config_filename
        self.view_message = None
        self.alert_message = None
        self.input_queue = Queue()  # Очередь для хранения нажатых клавиш
        self.input_thread_running = True
        self.input_thread = threading.Thread(target=self.input_output_thread_worker, daemon=True)


    def save_game_configs(self, filename=None):
        assert self.run_mode != "base"
        if filename is None:
            return

        with open(self.game_config_filename, "w+") as f:
            data = {"player": self.player_name,
                    "server": self.server,
                    "color": self.color,
                    "run_mode": self.run_mode,
                    "use_main_menu": self.use_main_menu}
            self.logger.debug(f"Saving game configs to {filename}:\n{data}")
            json.dump(data, f)

    def setup_logger(self, name, log_file, level=logging.INFO):
        """Настройка логгера"""
        self.logger = logging.getLogger(name)

        if not self.logging_level is None:
            self.logger.setLevel(level)
            file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')

            # To file
            if not self.logs_file is None:
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(file_formatter)
                self.logger.addHandler(file_handler)
            # To console
            console_handler = logging.StreamHandler(stdout)
            console_handler.setFormatter(console_formatter)


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
        self.view_message = data.get("data", "no died message recived")

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
    @abstractmethod
    def quit_session(self):
        pass
        # self.logger.debug("(in self.quit) Quiting...")
        # print("Quit.")
        # self.state = None
        # self.running = False
        # self.input_thread_running = False
    async def send(self, data: dict):
        if type(data) != dict:
            raise ValueError("data must be a dict")

        await self.websocket.send(json.dumps(dict))
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
                    self.quit_session()
                    return
            if self.is_message_for_send(message):
                # self.to_send.put({"type": "chat_message", "data": message})
                await self.websocket.send(json.dumps({"type": "chat_message", "data": message}))

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

    async def on_connect(self):
        await self.websocket.send(json.dumps({
            'name': self.player_name,
            'color': self.color
        }))
        self.state = "game"

        message = await asyncio.wait_for(self.websocket.recv(), timeout=0.1)
        data = json.loads(message)
        if data["type"] == "connection_error":
            raise ServerConnectionError(data["data"])

        self.player_id = data["player_id"]
    async def handle_websocket(self):
        try:
            message = await asyncio.wait_for(self.websocket.recv(), timeout=0.01)
            data = json.loads(message)
            await self.handle_data(data)
        except asyncio.TimeoutError:
            pass

    async def connect(self, uri):
        try:
            # self.logger.info(f"start connecting to {self.server_address}")
            async with websockets.connect(uri, ping_timeout=3, open_timeout=8) as websocket:
                self.logger.info(f"connected to {self.server}")

                self.websocket = websocket
                await self.on_connect()

                while self.is_game_session_now and self.running:
                    if self.is_me_alive() and self.state == "died":
                        self.state = "game"

                    await self.handle_websocket()

                    await self.handle_input()

                    while not self.to_send.empty():
                        await websocket.send(json.dumps(self.to_send.get()))
                # else:


        # except asyncio.CancelledError:
        #     self.logger.debug("async task connect() cancelled")
        #     raise

        finally:
            self.logger.debug("connection closed")

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

    def alert(self, title, message, instructions="....."):
        self.state = "alert"
        self.alert_message = (title, message, instructions)

    @abstractmethod
    async def wait_for_quit(self):
        """Бесконечно ожидаем, пока программа не завершится (self.state == None)"""

    @abstractmethod
    async def wait_for_end_session(self):
        pass

    async def connect_to_server(self):
        self.is_game_session_now = True
        try:
            self.logger.info(f"Starting connection. Server: {self.server}; name: {self.player_name}; color: {self.color}")
            self.logger.info(f"Trying connecting to {self.server}...")
            self.state = "connecting"
            self.view_message = f"Connecting to {self.server}"
            await self.connect(f"ws://{self.server}")


        except websockets.exceptions.ConnectionClosedOK:
            self.alert("Disconnected", "Server closed\nYou can try reconnect later")
            self.logger.warning("Disconnected, server closed")
            await self.wait_for_end_session()


        except (OSError, gaierror, ConnectionRefusedError, ConnectionError, websockets.exceptions.InvalidURI) as e:
            self.logger.error(f"{type(e).__name__}: {e}")
            self.state = "connection_error"
            self.view_message = (f"Connection error",
                       f"Error connecting to {self.server}\n\n{type(e).__name__}\n\n{e}", "press space")
            await self.wait_for_end_session()

        except ServerConnectionError as e:
            self.logger.warning(f"{type(e).__name__}: {e}")
            self.alert("Server send error", f"{type(e).__name__}: {e}", "press space")
            self.quit_session()

        except Exception as e:
            if type(e) == KeyboardInterrupt:
                raise KeyboardInterrupt
            traceback_str = traceback.format_exc()
            self.logger.critical(traceback_str)
            self.logger.critical(f"Game crashed. Error: {type(e).__name__}: {e}")
        finally:
            self.quit_session()
            self.logger.info("Session finished")

    async def run_game(self):
        # print(f"{Fore.GREEN}{self.ascii_logo}{Style.RESET_ALL}", end="")
        if self.run_mode in ["cli", "gui"]:
            self.logger.info(f"{Fore.LIGHTBLACK_EX}{Fore.LIGHTYELLOW_EX}Welcome to Multiplayer Snake {self.version}{Style.RESET_ALL}")
            self.logger.info(f"{Fore.LIGHTBLACK_EX}Powered by Arizel79 (https://github.com/Arizel79){Style.RESET_ALL}")
            self.logger.info(f"{Fore.LIGHTBLACK_EX}Source code: https://github.com/Arizel79/Multiplayer-snake-game{Style.RESET_ALL}")

        self.logger.debug(f"main menu? {'true' if self.use_main_menu else 'false'}")
        self.logger.debug(f"Logging level: {self.logging_level}")
        try:
            self.input_thread.start()
            if self.use_main_menu:
                while self.running:
                    while self.state == "main_menu" and self.running:
                        await asyncio.sleep(.01)
                    if self.state == "start_session":
                        await self.connect_to_server()
                        self.logger.info("Disconnected, backing to main menu...")

            else:
                await self.connect_to_server()
        except KeyboardInterrupt:
            self.logger.warning("KeyboardInterrupt received, shutting down...")
        finally:
            self.running = False
            self.input_thread_running = False

            if hasattr(self, 'input_thread') and self.input_thread.is_alive():
                self.input_thread.join(timeout=0.5)

            self.save_game_configs()