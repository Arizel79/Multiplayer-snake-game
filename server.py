import asyncio
import copy
import json
import random
from collections import deque
from dataclasses import dataclass, asdict

import websockets


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


class Server:
    def __init__(self, port, width=120, height=40):
        self.port = port

        self.width = width
        self.height = height

        self.snakes = {}
        self.food = []
        self.players = {}
        self.game_speed = 0.2
        self.max_food = width * height // 16

        self.connections = set()
    def get_avalible_coords(self):
        x1, y1, x2, y2 = self.get_map_rect()
        while True:
            x = random.randint(x1, x2)
            y = random.randint(y1, y2)
            p = (x, y)
            if not p in self.food:
                break
        return x, y
    def add_player(self, player_id:int, name, color):
        if player_id in self.snakes:
            return False

        x, y = self.get_avalible_coords()
        # Create snake body
        body = deque([Point(x, y)])
        for i in range(1, 3):
            body.append(Point(x - i, y))

        self.snakes[player_id] = Snake(
            body=body,
            direction='right',
            next_direction='right',
            color=color,
            name=name
        )
        self.players[player_id] = name
        return True

    def remove_player(self, player_id):
        #if player_id in self.snakes:
        #    del self.snakes[player_id]
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
        x1, y1, x2, y2 = self.get_map_rect()
        if len(self.food) < self.max_food:
            x = random.randint(x1, x2)
            y = random.randint(y1, y2)
            self.food.append(Point(x, y))

    def get_map_rect(self):
        x1, y1, x2, y2 = -(self.width // 2), -(self.height // 2), self.width // 2, self.height // 2
        return x1, y1, x2, y2

    def update(self):
        # Update directions
        for snake in self.snakes.values():
            snake.direction = snake.next_direction

        # Move snakes
        for snake_id, snake in list(self.snakes.items()):
            if not snake.alive:
                continue

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

            # Check collisions with walls
            # if (new_head.x < 0 or new_head.x >= self.width or
            #         new_head.y < 0 or new_head.y >= self.height):
            #     snake.alive = False
            #     continue

            # Check collisions with other snakes
            for other_snake in self.snakes.values():
                if new_head in other_snake.body:
                    snake.alive = False
                    break

            if not snake.alive:
                continue

            # Check if food eaten
            eaten = None
            for i, food in enumerate(self.food):
                if new_head.x == food.x and new_head.y == food.y:
                    eaten = i
                    snake.score += 1
                    break

            if eaten is not None:
                self.food.pop(eaten)
                snake.body.appendleft(new_head)
            else:
                snake.body.appendleft(new_head)
                snake.body.pop()

        # Remove dead snakes
        for snake_id in list(self.snakes.keys()):
            if not self.snakes[snake_id].alive:
                self.remove_player(snake_id)

        # Generate new food
        self.generate_food()
    def get_name_by_player_id(self, player_id):
        pass
    def to_dict(self):
        return {
            'type': "game_state",
            'map_borders': [i for i in self.get_map_rect()],
            'snakes': {pid: {
                'body': [asdict(p) for p in s.body],
                'color': s.color,
                'name': s.name,
                'score': s.score
            } for pid, s in self.snakes.items()},
            'food': [asdict(f) for f in self.food],
            'players': self.players
        }
    async def broadcast_chat_message(self, data):
        connections = copy.copy(self.connections)
        to_send = json.dumps(data)
        print(f"Send: {data}")
        for ws in connections:
            await ws.send(to_send)

    async def handle_client_chat_message(self, player_id, message: str):
        if message.startswith("/"):
            lst = message.split()
        else:
            nickname = "noname"
            await self.broadcast_chat_message({"type": "chat_message", "data": f"{message}", "from_user": f"{player_id}"})


    async def handle_client_data(self, player_id, data):
        print(f"Rec {player_id}: {data}")
        if data["type"] == "direction":
            self.change_direction(player_id, data['data'])
        elif data["type"] == "chat_message":
            await self.handle_client_chat_message(player_id, data["data"])

    async def handle_connection(self, websocket):
        print(1)
        self.connections.add(websocket)
        player_id = get_random_id()
        await websocket.send(json.dumps({"player_id": player_id, "type": "player_id"}))
        try:
            data = await websocket.recv()
            try:
                player_info = json.loads(data)
                name = player_info.get('name', 'Player')
                color = player_info.get('color', 'green')
                if not player_id:
                    await websocket.close()
                    return
                self.add_player(player_id, name, color)
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
            self.connections.discard(websocket)
            if player_id:
                self.remove_player(player_id)


    async def game_loop(self):
        while True:
            self.update()
            state = self.to_dict()

            # Send update to all connected clients
            connections_ = copy.copy(self.connections)
            for ws in connections_:
                try:
                    await ws.send(json.dumps(state))
                except Exception as e:
                    print(f"239 - {type(e).__name__}: e")

            await asyncio.sleep(self.game_speed)

    async def run(self):
        asyncio.create_task(self.game_loop())

        async with websockets.serve(self.handle_connection, "localhost", self.port):
            print(f"Server started at localhost:{self.port}")
            await asyncio.Future()

def get_random_id():
    return random.randint(0, 99999999)

async def main():
    game_state = Server(8090)
    await game_state.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass