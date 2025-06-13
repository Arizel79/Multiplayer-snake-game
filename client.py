import asyncio
import html
from queue import Queue, Empty
from pprint import pformat
import threading
import websockets
import json
from pyAsciiEngine import *
import argparse
import logging
from logging.handlers import RotatingFileHandler
from random import randint
from pyexpat.errors import messages

# Создаем логгер
logger = logging.getLogger('my_app')
logger.setLevel(logging.INFO)

# Создаем обработчик для ротации логов (макс. 5 файлов по 1 МБ каждый)
handler = RotatingFileHandler(
    'app.log',
    maxBytes=1024 * 1024,  # 1 MB
    encoding='utf-8'
)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Добавляем обработчик к логгеру
logger.addHandler(handler)
logger.info("start")


class Disconnected(Exception):
    pass


class SnakeGameClient:
    MAX_SHOWN_MESSAGES_CHAT_OFF = 6
    MAX_SHOWN_MESSAGES_CHAT_ON = 6

    def __init__(self, server_address=None, nickname=None, skin=None):
        self.show_debug = False
        self.server_address = server_address
        self.nickname = nickname
        self.skin = skin
        self.screen = ConsoleScreen()
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

        self.state = None

        self.alert_message = None
        self.input_queue = Queue()  # Очередь для хранения нажатых клавиш
        self.input_thread_running = True
        self.input_thread = threading.Thread(target=self._input_thread_worker, daemon=True)

    def _input_thread_worker(self):
        """Рабочая функция потока ввода, считывает клавиши и помещает их в очередь"""
        while self.input_thread_running:
            self.render()
            key = self.screen.get_key(.01)  # Блокирующий вызов с небольшим таймаутом
            if key is not None:
                self.input_queue.put(key)

    def get_game_map_coords_on_scr(self):
        x, y = self.screen.get_sizes()
        x1, y1, x2, y2 = 1, 1, x - 2, y - 2
        return x1, y1, x2, y2

    def handle_chat_message(self, message):
        from_user = message.get("from_user", None)
        if not from_user is None:
            self.add_chat_message(
                f"<blink><yellow>{html.escape(from_user)}</yellow><white>:</white> {html.escape(message.get('data', None))}</blink>")

    async def handle_data(self, data):
        logger.info(f"Data: {data}")
        if data.get("type", None) == "game_state":
            self.game_state = data
        elif data.get("type", None) == "chat_message":
            self.handle_chat_message(data)
        elif data.get("type", None) == "you_died":
            self.state = "died"
            self.alert_message = data.get("data", "no died message recived")
        else:
            assert False, data

    def is_message_for_send(self, messsage):
        if messsage == "/clear":
            return False
        return True

    async def send_chat(self):
        message = self.chat_prompt.lstrip()
        if message != "":

            if self.is_message_for_send(message):
                self.to_send.put({"type": "chat_message", "data": message})
            else:
                self.chat_messages.append(self.chat_prompt)
            self.chat_prompt = ""
            self.is_open_chat = False

    async def handle_input(self):
        try:
            while True:
                key = self.input_queue.get_nowait()  # Неблокирующее получение
                if self.state == "game":
                    if self.is_open_chat:
                        if key == "\x1b":
                            self.is_open_chat = False
                        elif key == "\x08":
                            if len(self.chat_prompt) > 0:
                                self.chat_prompt = self.chat_prompt[:-1]

                        elif key == "\n":
                            await self.send_chat()
                        else:
                            self.chat_prompt += key
                    else:
                        self.new_direction = None
                        if key == 'KEY_UP' or key == 'w':
                            self.new_direction = 'up'
                        elif key == 'KEY_DOWN' or key == 's':
                            self.new_direction = 'down'
                        elif key == 'KEY_LEFT' or key == 'a':
                            self.new_direction = 'left'
                        elif key == 'KEY_RIGHT' or key == 'd':
                            self.new_direction = 'right'
                        elif key == 'q':
                            self.running = False
                        elif key == "\t":
                            self.is_open_tablist = not self.is_open_tablist
                        elif key == "`":
                            self.show_debug = not self.show_debug
                        elif key == "z":
                            await self.websocket.send(json.dumps({"type": 'kill_me'}))
                        elif key.lower() == 't':
                            self.is_open_chat = True

                        if self.new_direction is not None and self.new_direction != self.direction:
                            # self.add_chat_message(str({"type": 'direction', "data": self.new_direction}))
                            await self.websocket.send(json.dumps({"type": 'direction', "data": self.new_direction}))
                            self.direction = self.new_direction
                            self.new_direction = None
                elif self.state == "alert":
                    if key == " ":
                        self.state = None

                elif self.state == "died":
                    if key == " ":
                        await self.websocket.send(json.dumps({"type": 'respawn', "data": "lol"}))
        except Empty:
            pass  # Очередь пуста, новых клавиш нет

        except KeyboardInterrupt:
            assert False, "in handle inpt"

    def add_chat_message(self, message):
        self.chat_messages.append(message)
    def is_me_alive(self):
        return bool(self.game_state) and self.game_state["snakes"][self.player_id]["alive"]
    async def connect(self, uri):
        async with websockets.connect(uri) as websocket:
            self.state = "game"
            self.websocket = websocket
            await websocket.send(json.dumps({
                'name': self.nickname,
                'color': self.player_color
            }))

            message = await asyncio.wait_for(websocket.recv(), timeout=0.1)
            data = json.loads(message)
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

    def render_tablist(self):
        x, y = self.screen.get_sizes()

        if self.is_open_tablist:

            tablist = f"\n<yellow>Server {self.server_address}</yellow>\n\nPlayers:\n"
            for k, v in self.game_state["players"].items():
                tablist += f"{v}\n"

            max_str = 0
            tablist = tablist.splitlines()
            for i in tablist:
                if len(i) > max_str:
                    max_str = len(i)
            tablist = "\n".join(tablist)
            self.screen.draw_rectangle((x // 2) - (max_str // 2), 0, (x // 2) + (max_str // 2),
                                       len(tablist.split("\n")), Symbol(" ", Colors.WHITE, Colors.BLACK, Styles.BLINK))

            self.screen.set_text(x // 2, 0, tablist, TextStyle(Colors.WHITE, Colors.BLACK, Styles.BLINK),
                                 parse_html=True,
                                 anchor_x=Anchors.CENTER_X_ANCHOR, anchor_y=Anchors.UP_ANCHOR)

    def render_game_world(self):
        if self.game_state is None:
            return
        x1, y1, x2, y2 = self.game_state["map_borders"]
        self.screen.draw_rectangle(*self.calc_coords(x1 - 1, y1 - 1), *self.calc_coords(x2 + 1, y2 + 1),
                                   Symbol("X", Colors.BLACK, Colors.BLACK, Styles.BLINK),
                                   isFill=False)

        for food in self.game_state['food']:
            self.screen.setSymbol(
                *self.calc_coords(food['x'], food['y']),
                '*',
                TextStyle("red", "black", "bold")
            )

        for snake_id, snake in self.game_state['snakes'].items():
            color = snake['color']
            head_style = TextStyle(color, "black", "bold")
            body_style = TextStyle(color, "black")

            for i, segment in enumerate(snake['body']):
                if i == 0:  # head
                    smbl = "0"
                    st = head_style
                else:
                    smbl = "o"
                    st = body_style
                self.screen.setSymbol(
                    *self.calc_coords(segment['x'], segment['y']),
                    smbl,
                    st
                )

    def render_chat(self):
        x, y = self.screen.get_sizes()
        if self.is_open_chat:
            self.screen.set_str(0, y - 1, f"> {self.chat_prompt.ljust(32)}",
                                TextStyle(Colors.WHITE, Colors.BLACK, Styles.BLINK))

        out = ""
        if self.is_open_chat:
            lst = self.chat_messages[-max(self.MAX_SHOWN_MESSAGES_CHAT_ON, len(self.chat_messages)):]
        else:
            lst = self.chat_messages[-max(self.MAX_SHOWN_MESSAGES_CHAT_OFF, len(self.chat_messages)):]

        for i in lst:
            if self.is_open_chat:
                out += f"<blink>{i}</blink>\n"
            else:
                out += f"<blink>{i[:min(80, len(i))]}</blink>\n"

        self.screen.set_text(0, y - 1, out, anchor_x=Anchors.LEFT_ANCHOR,
                             style=TextStyle(Colors.WHITE, Colors.BLACK),
                             anchor_y=Anchors.DOWN_ANCHOR, parse_html=True)

    def render(self):
        x, y = self.screen.get_sizes()

        # self.screen.clear()
        self.screen.clear()
        if self.state == "game":
            self.render_game_world()
            self.screen.set_text(0, 0, "Snake game by @Ariel79", TextStyle(Colors.YELLOW))
            x_, y_ = self.get_my_coords()
            self.screen.set_text(
                x, y,
                f"XY: {x_} {y_}", parse_html=True, anchor_x=Anchors.RIGHT_ANCHOR,
                anchor_y=Anchors.DOWN_ANCHOR)

            self.render_chat()

            self.render_tablist()
        elif self.state == "alert":
            render_alert(self.screen, self.alert_message)
        elif self.state == "died":
            text = f"""<red><bold>DIED</bold></red>

{self.alert_message}

Prees SPACE to respawn"""
            render_alert(self.screen, text)
        if self.show_debug:
            pretty_str = pformat(self.game_state)
            text = f"<cyan>DEBUG</cyan>\n{pretty_str}\n\n{self.chat_messages}"
            self.screen.set_text(x, 0, text, parse_html=True, anchor_x=Anchors.RIGHT_ANCHOR, anchor_y=Anchors.UP_ANCHOR)
        self.screen.update()

    def alert(self, title, message):
        self.state = "alert"
        self.alert_message = f"<bold>{title}</bold>\n\n{message}"

    async def run_game(self):
        try:
            self.input_thread.start()
            colors = ["green", "blue", "yellow", "magenta", "cyan", "white"]
            self.player_color = colors[int(self.skin)]

            try:
                self.alert(f"Connecting to {self.server_address}", "Please, wait...")
                await self.connect(f"ws://{self.server_address}")


            except websockets.exceptions.ConnectionClosedOK:
                self.alert("<red>Disconnected</red>", "Server closed")
                while self.state != None:
                    await asyncio.sleep(.1)
                    await self.handle_input()

            except Disconnected as e:
                self.alert("<red>Youre death</red>", f"Death...")
                while self.state != None:
                    await asyncio.sleep(.1)
                    await self.handle_input()
            except Exception as e:
                err = f"{type(e).__name__}: {str(e)}"
                logger.error(err)
                self.alert("<red>Disconnected</red>", f"{err}")
                while self.state != None:
                    await asyncio.sleep(.1)
                    await self.handle_input()

        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received, shutting down...")
        finally:
            # Корректное завершение
            self.running = False
            self.input_thread_running = False

            # Даем потоку немного времени на завершение
            if hasattr(self, 'input_thread') and self.input_thread.is_alive():
                self.input_thread.join(timeout=0.5)

            self.screen.quit()
            # Выходим из программы
            # raise SystemExit(0)


def prompt(sc, title="!prompt!", message="???", default="none"):
    style = TextStyle("white", "black")
    title_style = TextStyle("red", "black")
    input_style = TextStyle("green", "black")
    message_lines = message.splitlines()
    text = ""
    while True:
        sc.clear()
        sc.set_text(0, 0, title, title_style)
        y_ = 1
        for n, i in enumerate(message_lines):
            sc.set_text(0, y_, i, style)
            y_ += 1
        sc.set_text(0, y_, "> " + text, input_style)
        sc.update()

        key = sc.wait_key(0)
        if key == '\n':
            break
        elif key == '\b' or key == '\x7f':  # backspace
            text = text[:-1]
        elif isinstance(key, str) and len(key) == 1:
            text += key
    return text


def alert(scr, text):
    while True:
        render_alert(scr, text)
        key = scr.get_key()
        if key in [" ", "\n", "q"]:
            break


def render_alert(scr: ConsoleScreen, full_text):
    x, y = scr.get_sizes()
    scr.clear()
    scr.set_text(
        x // 2, y // 2,
        full_text, parse_html=True, anchor_x=Anchors.CENTER_X_ANCHOR, anchor_y=Anchors.CENTER_Y_ANCHOR
    )
    scr.update()


async def main():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument('--name', type=str, help='', default=f"player_{randint(0, 999)}")
    parser.add_argument('--skin', type=str, help='', default="2")
    parser.add_argument('--address', type=str, help='Server address', default="localhost:8090")
    args = parser.parse_args()

    g = SnakeGameClient(args.address, args.name, args.skin)
    await g.run_game()
    # await run_game(args.address, args.name, args.skin)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
