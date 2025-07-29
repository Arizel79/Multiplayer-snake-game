import argparse
import html
from random import randint, choice

from client_base import *

from pyAsciiEngine import *


class ClientCLI(ClientBase):
    SNAKE_COLORS = ["red", "green", "blue", "yellow", "magenta", "cyan"]

    def __init__(self, *args, interactive=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.version = f"{self.version} (CLI)"
        if interactive:
            self.logger.info("Interactive prompting enabled")
            self.nickname = input("Nickname: ")
            self.color = input("Color: ")
            self.server_address = input("Server IP: ")

    def input_output_thread_worker(self):

        try:
            self.screen = ConsoleScreen()
            """Рабочая функция потока ввода, считывает клавиши и помещает их в очередь"""
            while self.input_thread_running:
                self.render()
                key = self.screen.get_key(.001)  # Блокирующий вызов с небольшим таймаутом
                if key is not None:
                    self.input_queue.put(key)

        finally:
            self.quit()
            self.screen.quit()

    async def handle_input(self):
        try:
            while True:
                key = self.input_queue.get_nowait()
                key_ = key.lower()
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
                            if len(key) == 1:
                                self.chat_prompt += key
                    else:
                        self.new_direction = None
                        if key_ in ["w", "ц"]:
                            self.new_direction = 'up'
                        elif key_ in ["s", "ы"]:
                            self.new_direction = 'down'
                        elif key_ in ["a", "ф"]:
                            self.new_direction = 'left'
                        elif key_ in ["d", "в"]:
                            self.new_direction = 'right'
                        elif key in ["Q"]:
                            self.logger.info("Received Q, exiting...")
                            self.running = False
                        elif key == "\t":
                            self.is_open_tablist = not self.is_open_tablist
                        elif key == "`":
                            self.show_debug = not self.show_debug

                        elif key_ in ['t', "е"]:
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
            self.quit()


    def get_params(self, player_id, with_header=True):
        sn = self.game_state["snakes"][player_id]
        pl = self.game_state["players"][player_id]
        header = ""
        if with_header:
            header = f"-----[{self.get_stilizate_name_color(player_id)}]-----\n"
        out = f"""{header}Size: {sn["size"]}
Max size: {sn["max_size"]}
Total kills: {pl["kills"]}
Total deaths: {pl["deaths"]}
{'-' * len(remove_html_tags(header))}"""
        return out

    async def wait_for_end(self):
        while self.state != None:
            await asyncio.sleep(.01)
            await self.handle_input()

    def render(self):
        x, y = self.screen.get_sizes()

        # self.screen.clear()
        self.screen.clear()
        if self.state == "game" and (not self.game_state  is None):
            self.render_game_world()
            x_, y_ = self.get_my_coords()
            self.screen.set_text(0, 0, "<bold>Multiplayer snake game</bold>\n"
                                       f"xy: {x_}, {y_}\n"
                                       f"size: <bold><cyan>{str(self.game_state.get('snakes', {}).get(self.player_id, {}).get('size'))}</cyan></bold>",
                                 TextStyle(Colors.WHITE, Colors.BLACK), parse_html=True)

            self.screen.set_text(
                x, y,
                f"^C to quit; h to help", parse_html=True, anchor_x=Anchors.RIGHT_ANCHOR,
                anchor_y=Anchors.DOWN_ANCHOR)

            self.render_chat()

            self.render_tablist()
        elif self.state == "alert":
            render_alert(self.screen, self.alert_message)
        elif self.state == "died":
            text = f"""<red><bold>You died</bold></red>

{self.alert_message}

{self.get_params(self.player_id)}

<b>Prees SPACE to respawn</b>"""
            render_alert(self.screen, text)
        if self.show_debug:
            pretty_str = self.game_state
            text = f"<cyan>DEBUG</cyan>\n{self.state}\n{pretty_str}\n\n{self.chat_messages}"
            self.screen.set_text(x, 0, text, parse_html=True, anchor_x=Anchors.RIGHT_ANCHOR,
                                 anchor_y=Anchors.UP_ANCHOR)
        self.screen.update()

    def get_stilizate_name_color(self, player_id, text=None):
        color = self.game_state["players"].get(player_id, {})["color"]
        if text == None:
            text = self.game_state["players"].get(player_id, {})["name"]

        if color not in self.SNAKE_COLORS:
            color = "white"

        return f"<{color}>{text}</{color}>"

    def handle_chat_message(self, message):
        from_user = message.get("from_user", None)
        subtype = message.get("subtype", "chat_message")

        if subtype == "death_message":
            self.add_chat_message(f"<red>[DEATH]</red> {message.get('data', None)}")
        if subtype == "join/left":
            self.add_chat_message(f"{message.get('data', None)}")
        elif subtype == "chat_message":
            if not from_user is None:
                self.add_chat_message(
                    f"{from_user}<white>:</white> {html.escape(message.get('data', None))}")
            elif from_user in ["", None]:
                self.add_chat_message(f"{message.get('data', None)}")

    def render_tablist(self):
        x, y = self.screen.get_sizes()

        if self.is_open_tablist:
            alive_count = 0
            dead_count = 0
            for player_id, player in self.game_state["players"].items():
                if player["alive"]:
                    alive_count += 1
                else:
                    dead_count += 1
            tablist = f"\n<yellow>Server {self.server_address}</yellow>\n{self.server_desc}\n\nPlayers ({len(self.game_state['players'])})\n(<green>Alive: {alive_count}</green> | <red>Dead: {dead_count}</red>):\n"

            for player_id, player in self.game_state["players"].items():
                sn = self.game_state["snakes"][player_id]
                death_flag = ""
                params = f"[S: {sn['size']}; MAX: {sn['max_size']}; D: {player['deaths']}; K: {player['kills']}]"
                if not player["alive"]:
                    death_flag = "<red>[DEATH]</red> "
                if player_id == self.player_id:
                    tablist += f"<cyan>[ME]</cyan> {death_flag}{self.get_stilizate_name_color(player_id)} {params}"
                else:
                    tablist += f"{death_flag}{self.get_stilizate_name_color(player_id)} {params}"
                tablist += "\n"
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

    def get_snake_color_segment(self, color, segment_n):
        if segment_n == 0:
            return Symbol("0", color, Colors.BLACK, Styles.DIM)
        else:
            return Symbol("o", color, Colors.BLACK)

    def render_game_world(self):
        if self.game_state is None:
            return
        x1, y1, x2, y2 = self.game_state["map_borders"]
        self.screen.draw_rectangle(*self.calc_coords(x1 - 1, y1 - 1), *self.calc_coords(x2 + 1, y2 + 1),
                                   Symbol("X", Colors.BLACK, Colors.BLACK, Styles.BLINK),
                                   isFill=False)
        # Death snakes
        for snake_id, snake in self.game_state['snakes'].items():
            if snake["alive"]:
                continue
            # color = snake['color']
            death_symbol = Symbol("D", Colors.BLACK, Colors.BLACK, Styles.BLINK)

            for i, segment in enumerate(snake['body'][::-1]):
                self.screen.set_symbol_obj(
                    *self.calc_coords(segment['x'], segment['y']),
                    death_symbol
                )

        # Food
        for food in self.game_state['food']:
            self.screen.setSymbol(
                *self.calc_coords(food['x'], food['y']),
                '*',
                TextStyle("red", "black", "bold")
            )
        # Alive snakes
        for snake_id, snake in self.game_state['snakes'].items():
            if not snake["alive"]:
                continue
            color = snake['color']
            death_symbol = Symbol("D", Colors.BLACK, Colors.BLACK, Styles.BLINK)

            for i, segment in enumerate(snake['body'][::-1]):
                smbl = self.get_snake_color_segment(snake["color"], len(snake['body']) - i - 1)
                self.screen.set_symbol_obj(
                    *self.calc_coords(segment['x'], segment['y']),
                    smbl
                )


    def render_chat(self):
        x, y = self.screen.get_sizes()
        if self.is_open_chat:
            self.screen.set_str(0, y - 1, f"> {self.chat_prompt.ljust(32)}",
                                TextStyle(Colors.WHITE, Colors.BLACK, Styles.BLINK))

        out = ""
        if self.is_open_chat:
            lst = self.chat_messages[-min(self.MAX_SHOWN_MESSAGES_CHAT_ON, len(self.chat_messages)):]
        else:
            lst = self.chat_messages[-min(self.MAX_SHOWN_MESSAGES_CHAT_OFF, len(self.chat_messages)):]

        for i in lst:
            if self.is_open_chat:
                out += f"{i}\n"
            else:
                out += f"{i[:min(1024, len(i))]}\n"

        self.screen.set_text(0, y - 1, out, anchor_x=Anchors.LEFT_ANCHOR,
                             style=TextStyle(Colors.WHITE, Colors.BLACK, ),
                             anchor_y=Anchors.DOWN_ANCHOR, parse_html=True)


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


def remove_html_tags(text):
    clean_text = re.sub(r'<[^>]*>', '', text)
    return clean_text


def render_alert(scr: ConsoleScreen, full_text):
    x, y = scr.get_sizes()
    scr.clear()
    scr.set_text(
        x // 2, y // 2,
        full_text, parse_html=True, anchor_x=Anchors.CENTER_X_ANCHOR, anchor_y=Anchors.CENTER_Y_ANCHOR
    )
    scr.update()


async def run_client():
    parser = argparse.ArgumentParser(description="Multiplayer Snake game")
    parser.add_argument('--name', "--n", type=str, help='Snake name', default=f"player_{randint(0, 99999)}")
    parser.add_argument('--color', "--c", type=str, help='Snake color', default=choice(ClientCLI.SNAKE_COLORS))
    parser.add_argument('--server', "--s", type=str, help='Server address', default="localhost:8090")
    parser.add_argument('--log_lvl', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Level of logging', default="INFO")
    parser.add_argument("--interactive", "--i", action="store_true", help = "Enable interactive prompting (default: False)")
    args = parser.parse_args()

    g = ClientCLI(args.server, args.name, args.color, logging_level=args.log_lvl, interactive=args.interactive)
    await g.run_game()
    # await run_game(args.address, args.name, args.skin)


def main():
    try:
        asyncio.run(run_client())
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
