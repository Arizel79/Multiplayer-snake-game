import asyncio
import websockets
import json
from pyAsciiEngine import *


class SnakeGameClient:
    def __init__(self):
        self.screen = AsciiScreen()
        self.player_id = None
        self.player_name = "Player"
        self.player_color = "green"
        self.game_state = None
        self.last_key = None
        self.running = True

    async def connect(self, uri):
        async with websockets.connect(uri) as websocket:
            # Send player info
            await websocket.send(json.dumps({
                'id': str(id(self)),
                'name': self.player_name,
                'color': self.player_color
            }))

            # Start receiving updates
            while self.running:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                    self.game_state = json.loads(message)
                except asyncio.TimeoutError:
                    pass

                # Handle input
                key = self.screen.get_key(0)
                if key is not None:
                    direction = None
                    if key == 'KEY_UP' or key == 'w':
                        direction = 'up'
                    elif key == 'KEY_DOWN' or key == 's':
                        direction = 'down'
                    elif key == 'KEY_LEFT' or key == 'a':
                        direction = 'left'
                    elif key == 'KEY_RIGHT' or key == 'd':
                        direction = 'right'
                    elif key == 'q':
                        self.running = False

                    if direction is not None:
                        try:
                            await websocket.send(json.dumps({'direction': direction}))
                        except:
                            pass

                # Render game
                self.render()

    def render(self):
        if not self.game_state:
            return

        self.screen.clear()

        # Draw border

        # Draw food
        self.screen.setStr(0, 0, "Snake game by @Ariel79", TextStyle(Colors.YELLOW))
        x_, y_ = 1, 2
        # self.screen.drawRectangle(x_, y_, self.game_state['width'], self.game_state['height'], Symbol("_"), isFill=False)
        for food in self.game_state['food']:
            self.screen.setSymbol(
                food['x'] + x_, food['y'] + y_,
                '@',
                TextStyle("red", "black", "bold")
            )

        # Draw snakes
        for snake_id, snake in self.game_state['snakes'].items():
            color = snake['color']
            head_style = TextStyle(color, "black", "bold")
            body_style = TextStyle(color, "black")

            for i, segment in enumerate(snake['body']):
                if i == 0:  # head
                    self.screen.setSymbol(
                        segment['x'] + x_, segment['y'] + y_,
                        'O',
                        head_style
                    )
                else:  # body
                    self.screen.setSymbol(
                        segment['x'] + x_, segment['y'] + y_,
                        'o',
                        body_style
                    )

        self.screen.drawRectangle(x_ - 1, y_ - 1, x_ + self.game_state["width"] + 1, y_ + self.game_state["height"] + 1,
                                  Symbol("."),
                                  isFill=False)

        y = y_ + self.game_state["height"] + 1
        y += 1
        self.screen.setText(
            0, y,
            "Scores:",
            TextStyle("white", "black", "bold")
        )
        y += 1

        for snake_id, snake in self.game_state['snakes'].items():
            is_you = snake_id == str(id(self))
            prefix = "[you] " if is_you else ""
            self.screen.setText(
                0, y,
                f"{prefix}{snake['name']}: {snake['score']}",
                TextStyle(snake['color'], "black", "bold" if is_you else "normal")
            )
            y += 1
        # Controls info
        self.screen.setText(
            0, y,
            "Controls: WASD/Arrows - Move, Q - Quit",
            TextStyle("cyan", "black")
        )
        self.screen.update()


def prompt(sc, title="  prompt", message="", default="none"):
    # Get player name

    style = TextStyle("white", "black")
    title_style = TextStyle("red", "black")
    input_style = TextStyle("green", "black")
    message_lines = message.splitlines()
    text = ""
    while True:
        sc.clear()
        sc.setText(0, 0, title, title_style)
        y_ = 1
        for n, i in enumerate(message_lines):
            sc.setText(0, y_, i, style)
            y_ += 1
        sc.setText(0, y_, "> " + text, input_style)
        sc.update()

        key = sc.wait_key()
        if key == '\n':
            break
        elif key == '\b' or key == '\x7f':  # backspace
            text = text[:-1]
        elif isinstance(key, str) and len(key) == 1:
            text += key
    return text


async def main():
    print("Connecting to server...")
    client = SnakeGameClient()

    name = prompt(client.screen, "Name:", "")

    client.player_name = name if name else "Player"

    # Get player color
    colors = ["green", "blue", "yellow", "magenta", "cyan", "white"]
    client.screen.clear()
    client.screen.setText(0, 0, "Choose your color:", TextStyle("white", "black"))

    for i, color in enumerate(colors):
        client.screen.setText(
            0, i + 1,
            f"{i + 1}. {color}",
            TextStyle(color, "black")
        )

    client.screen.update()

    while True:
        key = client.screen.wait_key()
        if key in ['1', '2', '3', '4', '5', '6']:
            idx = int(key) - 1
            if idx < len(colors):
                client.player_color = colors[idx]
                break

    # Connect to server
    try:
        await client.connect("ws://localhost:8765")
    except Exception as e:
        client.screen.clear()
        client.screen.setText(
            0, 0,
            f"Connection error: {str(e)}",
            TextStyle("red", "black")
        )
        client.screen.update()
        client.screen.wait_key()


if __name__ == "__main__":
    asyncio.run(main())
