import asyncio
import copy
import json
import random
from collections import deque
from dataclasses import dataclass, asdict
from random import randint
import websockets
from string import ascii_letters, digits
from time import time
import argparse
import logging
import sys


@dataclass
class Point:
    x: int
    y: int


@dataclass
class Snake:
    body: deque
    direction: str
    next_direction: str
    color: str
    name: str
    score: int = 0
    alive: bool = True
    is_fast: str = False



@dataclass
class Player:
    player_id: str
    name: str
    color: str
    alive: bool
    deaths: int = 0
    kills: int = 0


class Server:
    VALID_NAME_CHARS = ascii_letters + digits + "_"

    DEFAULT_SNAKE_LENGHT = 5
    SNAKE_COLORS = ["red", "green", "blue", "yellow", "magenta", "cyan"]

    NORMAL_SNAKE_SPEED = 0.3  # каждые 0.3 сек двигаемся
    FAST_SNAKE_SPEED = 0.1

    def __init__(self, port, map_width=80, map_height=40, max_players=20, max_food=50,
                 server_name="Test Server", server_desc=None, logging_level="debug",
                 max_food_perc=10):
        self.port = port

        self.width = map_width
        self.height = map_height

        self.snakes = {}
        self.food = []
        self.players = {}
        self.max_players = max_players

        self.game_speed = 0.2
        self.max_food_relative = max_food_perc / 100
        self.max_food = (self.width * self.height) * self.max_food_relative
        self.lost_perc = 1
        self.connections = {}
        if server_desc is None:
            self.server_desc = f"<green>Welcome to our the {server_name}!</green"
        else:
            self.server_desc = server_desc

        self.old_tick_time = time()
        self.TICK_SPEED = 0.05  # sec

        self.last_normal_snake_move_time = time()
        self.last_fast_snake_move_time = time()

        self.logging_level = logging_level
        self.setup_logger(__name__, "server.log", getattr(logging,self.logging_level))
        self.logger.info(f"Logging level: {self.logging_level}")
    async def set_server_desc(self, server_desc):
        self.server_desc = server_desc
        await self.broadcast_chat_message({"type": "set_server_desc",
                                           "data": self.server_desc})

    def setup_logger(self, name, log_file='server.log', level=logging.INFO):
        """Настройка логгера с выводом в консоль и файл."""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_formatter = logging.Formatter('[%(levelname)s] %(message)s')

        # Обработчик для записи в файл
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(file_formatter)

        # Обработчик для вывода в консоль
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        return self.logger

    def get_all_food_count(self):
        food_count = 0
        food_count += len(self.food)

        for k, v in self.snakes.items():
            food_count += len(v.body)
        return food_count

    def get_avalible_coords(self):
        x1, y1, x2, y2 = self.get_map_rect()
        while True:
            x = random.randint(x1, x2)
            y = random.randint(y1, y2)
            p = (x, y)
            if not p in self.food:
                break
        return x, y
    def get_addres_from_ws(self, ws):
        return ":".join(str(i) for i in ws.remote_address)
    async def add_player(self, player_id: str, name, color):
        if player_id in self.snakes:
            return False
        self.players[player_id] = Player(
            player_id=player_id,
            name=name,
            color=color,
            alive=True)

        await self.spawn(player_id)
        await self.broadcast_chat_message({"type": "chat_message", "subtype": "join/left",
                                           "data": f"<yellow>[</yellow><green>-</green><yellow>]</yellow> {await self.get_stilizate_name_color(player_id)} <yellow>joined the game</yellow>"})
        self.logger.info(f"Connection {self.get_addres_from_ws(self.connections[player_id])} registred as {self.get_player(player_id)}")
        return True

    async def remove_player(self, player_id):
        await self.broadcast_chat_message({"type": "chat_message", "subtype": "join/left",
                                           "data": f"<yellow>[</yellow><red>-</red><yellow>]</yellow> {await self.get_stilizate_name_color(player_id)} <yellow>left the game</yellow>"})

        if player_id in self.snakes:
            del self.snakes[player_id]
        if player_id in self.players:
            del self.players[player_id]

    def change_direction(self, player_id, direction):
        if player_id in self.snakes:
            snake = self.snakes[player_id]
            # Prevent 180-degree turns
            if (direction == 'up' and snake.direction != 'down') or \
                    (direction == 'down' and snake.direction != 'up') or \
                    (direction == 'left' and snake.direction != 'right') or \
                    (direction == 'right' and snake.direction != 'left'):
                snake.next_direction = direction

    def generate_food(self):
        if self.get_all_food_count() < self.max_food:
            x1, y1, x2, y2 = self.get_map_rect()
            if len(self.food) < self.max_food:
                x = random.randint(x1, x2)
                y = random.randint(y1, y2)
                self.food.append(Point(x, y))

    def get_player(self, player_id):
        return f"{self.players[player_id].name} ({player_id})"

    async def player_death(self, player_id, reason: str = "No reason"):
        self.logger.info(f"Player {self.get_player(player_id)} death ({reason})")

        self.snakes[player_id].alive = False
        body = self.snakes[player_id].body
        del self.snakes[player_id]
        self.players[player_id].alive = False
        self.players[player_id].deaths += 1
        state = self.to_dict()
        ws = self.connections[player_id]
        await ws.send(json.dumps(state))
        await self.connections[player_id].send(json.dumps({"type": "you_died", "data": reason}))
        await self.broadcast_chat_message({"type": "chat_message", "subtype": "death_message",
                                           "data": f'{await self.get_stilizate_name_color(player_id)} {reason}'})
        for i in body:
            self.food.append(i)
        # del self.snakes[player_id]
        # del self.players[player_id]

    def get_map_rect(self):
        x1, y1, x2, y2 = -(self.width // 2), -(self.height // 2), self.width // 2, self.height // 2
        return x1, y1, x2, y2

    def is_name_valid(self, name: str):
        if len(name) > 16:
            return "Nickname is too long"
        elif len(name) < 4:
            return "Nickname is too short"

        for i in name:
            if i.lower() not in self.VALID_NAME_CHARS:
                return "Nickname contain invalid characters"

        return True

    async def update(self):

        self.generate_food()

        for snake in self.snakes.values():
            snake.direction = snake.next_direction

        # Move snakes
        now = time()
        move_fast, move_normal = False, False
        # print("self.last_normal_snake_move_time + self.NORMAL_SNAKE_SPEED",self.last_normal_snake_move_time + self.NORMAL_SNAKE_SPEED, now)
        if self.last_normal_snake_move_time + self.NORMAL_SNAKE_SPEED >= now:
            self.last_normal_snake_move_time = now
            move_normal = True


        elif self.last_fast_snake_move_time + self.FAST_SNAKE_SPEED >= now:
            self.last_fast_snake_move_time = now
            move_fast = True

        if move_fast or move_normal:
            for player_id, snake in list(self.snakes.items()):
                if not snake.alive:
                    continue
                    print(f"Death snake detect: {snake}")
                if snake.is_fast and move_fast:
                    print(f"MOVE SNAKE-fast {player_id}")
                    head = snake.body[0]
                    new_head = Point(head.x, head.y)

                    if snake.direction == 'up':
                        new_head.y -= 1
                    elif snake.direction == 'down':
                        new_head.y += 1
                    elif snake.direction == 'left':
                        new_head.x -= 1
                    elif snake.direction == 'right':
                        new_head.x += 1

                elif (not snake.is_fast) and move_normal:
                    head = snake.body[0]
                    new_head = Point(head.x, head.y)

                    if snake.direction == 'up':
                        new_head.y -= 1
                    elif snake.direction == 'down':
                        new_head.y += 1
                    elif snake.direction == 'left':
                        new_head.x -= 1
                    elif snake.direction == 'right':
                        new_head.x += 1

                else:
                    continue

                walls = self.get_map_rect()

                if (new_head.x < walls[0] or new_head.x > walls[2] or
                        new_head.y < walls[1] or new_head.y > walls[3]):
                    await self.player_death(player_id, "Сrashed into the border of the world (really?)")
                    continue

                # Check collisions with other snakes
                snakes = copy.copy(self.snakes)
                for other_snake_id, other_snake in snakes.items():
                    if new_head in other_snake.body and (not other_snake is snake):
                        await self.player_death(player_id, f'Crashed into "{other_snake.name}" snake')
                        self.players[other_snake_id].kills += 1
                        continue

                if not snake.alive:
                    continue

                # Check if food eaten
                eaten = None
                # print("body", snake.body)
                remove_end = True
                for i, food in enumerate(self.food):
                    if new_head.x == food.x and new_head.y == food.y:
                        eaten = i
                        snake.score += 1

                        if eaten is not None:
                            self.food.pop(eaten)
                            remove_end = False
                            break
                        else:
                            break
                snake.body.appendleft(new_head)
                if remove_end:
                    snake.body.pop()

                # await self.steal_body(player_id)
                # await self.steal_body(snake_id)



        else:
            return

        for player_id, snake in list(self.snakes.items()):
            if not snake.alive:
                continue

    def to_dict(self):
        return {
            'type': "game_state",
            'map_borders': [i for i in self.get_map_rect()],
            'snakes': {pid: {
                'body': [asdict(p) for p in s.body],
                'color': s.color,
                'name': s.name,
                'score': s.score,
                'alive': s.alive,

            } for pid, s in self.snakes.items()},
            'food': [asdict(f) for f in self.food],
            'players': {pid: {"name": pl.name,
                              "color": pl.color,
                              "alive": pl.alive,
                              "kills": pl.kills,
                              "deaths": pl.deaths,
                              } for pid, pl in self.players.items()}
        }

    async def broadcast_chat_message(self, data):
        connections_ = copy.copy(self.connections)
        to_send = json.dumps(data)
        self.logger.debug(f"Broadcast data: {data}")

        for plaier_id, ws in connections_.items():
            await ws.send(to_send)

    async def get_stilizate_name_color(self, player_id, text=None):

        color = self.players.get(player_id, {}).color
        if text == None:
            text = self.players.get(player_id).name

        if color in self.SNAKE_COLORS:
            pass
        else:
            color = "white"

        return f"<{color}>{text}</{color}>"

    async def handle_client_chat_message(self, player_id, message: str):
        con = self.connections[player_id]
        if message.startswith("/"):
            lst = message.split()
            if lst[0] == "/help":
                await con.send(json.dumps({"type": "chat_message",
                                           "data": f"Help mesaage here?"}))
            elif lst[0] == "/kill":
                await self.player_death(player_id, "kill command")
        else:
            name = self.players[player_id].name
            await self.broadcast_chat_message(
                {"type": "chat_message", "data": f"{message}",
                 "from_user": f"{await self.get_stilizate_name_color(player_id)}"})

    async def handle_client_data(self, player_id: str, data: dict):
        self.logger.debug(f"Recieved data from {self.get_player(player_id)}: {data}")
        if data["type"] == "direction":
            self.change_direction(player_id, data['data'])
        elif data["type"] == "chat_message":
            await self.handle_client_chat_message(player_id, data["data"])
        elif data["type"] == "kill_me":
            await self.player_death(player_id)
        elif data["type"] == "respawn":
            await self.respawn(player_id)

    async def spawn(self, player_id, lenght=DEFAULT_SNAKE_LENGHT):
        x, y = self.get_avalible_coords()
        # Create snake body
        body = deque([Point(x, y)])
        for i in range(1, lenght):
            body.append(Point(x - i, y))

        self.snakes[player_id] = Snake(
            body=body,
            direction='right',
            next_direction='right',
            color=self.players[player_id].color,
            name=self.players[player_id].name,
            alive=True,

        )
        self.players[player_id].alive = True

    async def respawn(self, player_id):
        self.logger.info(f"Respawn {self.get_player(player_id)} ({self.players[player_id].name})")
        await self.spawn(player_id)

    async def handle_connection(self, websocket):
        self.logger.debug(f"{websocket.remote_address} is trying to connect to the server")
        while True:
            player_id = get_random_id()
            if not (player_id in self.players.keys()):
                self.logger.debug(f"{websocket.remote_address}`s player_id={player_id}")
                break
        self.connections[player_id] = websocket
        await websocket.send(json.dumps({"player_id": player_id, "type": "player_id"}))
        try:
            data = await websocket.recv()
            try:
                player_info = json.loads(data)
                name = player_info.get('name', 'Player')
                name_valid = self.is_name_valid(name)
                if not name_valid is True:
                    await websocket.send(json.dumps({"type": "connection_error",
                                                     "data": f"Invalid name: {name_valid}"}))
                    return

                color = player_info.get('color', 'green')
                if not color in self.SNAKE_COLORS:
                    await websocket.send(json.dumps({"type": "connection_error",
                                                     "data": f"Invalid snake color\nValid colors: {', '.join(self.SNAKE_COLORS)}"}))
                    return

                await self.add_player(player_id, name, color)
                await websocket.send(json.dumps({"type": "set_server_desc", "data": self.server_desc}))
                await websocket.send(json.dumps(self.to_dict()))
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        await self.handle_client_data(player_id, data)
                    except:
                        pass

            except (json.JSONDecodeError, websockets.exceptions.ConnectionClosedError):
                await websocket.close()
                return


        finally:
            await websocket.close()
            del self.connections[player_id]
            await self.remove_player(player_id)

    async def steal_body(self, player_id):
        return
        self.logger.debug(f"Stealing body from {self.get_player(player_id)}")
        snake = self.snakes[player_id]
        if random.random() < self.lost_perc:
            if len(snake.body) > 5:
                snake.body.pop()

    async def on_tick(self):
        for player_id, pl in self.players.items():
            pass
            # await self.steal_body(player_id)

    async def game_loop(self):

        while True:
            await self.update()
            now = time()
            if now >= self.old_tick_time + self.TICK_SPEED:
                self.old_tick_time = now
                await self.on_tick()
            state = self.to_dict()

            connections_ = copy.copy(self.connections)
            for player_id, ws in connections_.items():
                try:
                    await ws.send(json.dumps(state))

                except Exception as e:
                    print(f"239 - {type(e).__name__}: e")

            await asyncio.sleep(self.game_speed)

    async def run(self):
        asyncio.create_task(self.game_loop())
        try:
            async with websockets.serve(self.handle_connection, "localhost", self.port):
                print(f"Server started at localhost:{self.port}")
                # self.logger.info(f"Server started at localhost:{self.port}")

                await asyncio.Future()
        except OSError as e:
            self.logger.fatal(f"OSError: {e}")


def get_random_id():
    return str(random.randint(0, 99999999))


async def main():
    parser = argparse.ArgumentParser(description="Multiplayer Snake game by @Arizel79 (server)")
    parser.add_argument('--port', type=int, help='Server port', default=8090)
    parser.add_argument('--server_name', type=str, help='Server name', default="Server11")
    parser.add_argument('--server_desc', type=str, help='Description of server', default=None)
    parser.add_argument('--max_players', type=int, help='Max online players count', default=20)
    parser.add_argument('--map_width', type=int, help='Width of server map', default=60)
    parser.add_argument('--map_height', type=int, help='Height of server map', default=30)
    parser.add_argument('--food_perc', type=int, help='Proportion food/map in %', default=10)
    parser.add_argument('--log_lvl', type=str.upper, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Level of logging: DEBUG/INFO/WARNING/ERROR/CRITICAL', default="INFO")
    args = parser.parse_args()



    game_state = Server(port=args.port, map_width=args.map_width, map_height=args.map_height,
                        max_players=args.max_players, server_name=args.server_name, server_desc=args.server_desc,
                        max_food_perc=args.food_perc, logging_level=args.log_lvl)
    await game_state.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
