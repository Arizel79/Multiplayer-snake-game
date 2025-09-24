import asyncio
import copy
import json
import random
from collections import deque
from dataclasses import dataclass
from pprint import pprint
from random import randint, choice
import websockets
import ssl
from time import time
import argparse
import logging
import sys
import traceback

from config import *

prnt = print




@dataclass
class Point:
    x: int
    y: int

@dataclass
class Food:
    point: Point
    type_: int
    color: str
    size: int



@dataclass
class Snake:
    body: deque
    direction: str
    next_direction: str
    color: str
    name: str
    size: int = 0
    max_size: int = size
    alive: bool = True
    is_fast: str = False
    immortal: bool = False

    def remove_segment(self, n=1, min_pop_size=2):
        for i in range(n):
            if len(self.body) > min_pop_size:
                self.body.pop()
                self.size = len(self.body)

    def add_segment(self, n=1):
        if n < 0:
            raise ValueError("Argument 'n' must be natural integer. ")
        for i in range(n):
            self.body.append(copy.copy(self.body[-1]))
        self.size = len(self.body)
        if len(self.body) > self.max_size:
            self.max_size = len(self.body)


@dataclass
class Player:
    player_id: str
    name: str
    color: str
    alive: bool
    deaths: int = 0
    kills: int = 0
    best_score: int = 0
    last_score: int = 0

@dataclass
class Viewport:
    center_x: int
    center_y: int
    width: int
    height: int

    @property
    def left(self):
        return self.center_x - self.width // 2

    @property
    def right(self):
        return self.center_x + self.width // 2

    @property
    def top(self):
        return self.center_y - self.height // 2

    @property
    def bottom(self):
        return self.center_y + self.height // 2

    def contains_point(self, point: Point) -> bool:
        return (self.left <= point.x <= self.right and
                self.top <= point.y <= self.bottom)

    def intersects_snake(self, snake: Snake) -> bool:
        """Проверяет, пересекается ли змея с областью видимости"""
        for segment in snake.body:
            if self.contains_point(segment):
                return True
        return False


class Server:
    def __init__(self, address, port, map_width=80, map_height=80, max_players=20,
                 server_name="Server", server_desc=None, logging_level="debug",
                 max_food_perc=10, default_move_timeout=0.3, fast_move_timeout=0.1):
        self.port = port
        self.address = address

        self.width = map_width
        self.height = map_height

        self.snake_colors = DEAFULT_SNAKE_COLORS

        self.DEFAULT_MOVE_TIMEOUT = default_move_timeout
        self.FAST_MOVE_TIMEOUT = fast_move_timeout

        self.VALID_NAME_CHARS = VALID_NAME_CHARS

        self.snakes = {}
        self.food = []
        self.players = {}
        self.max_players = max_players
        self.connections = {}

        if server_desc is None:
            self.server_desc = f"<green>Welcome to our Server {server_name}!</green>"
        else:
            self.server_desc = server_desc

        self.game_speed = 0.01
        self.max_food_relative = max_food_perc / 100
        self.max_food = (self.width * self.height) * self.max_food_relative

        self.min_steling_snake_size = 5
        self.stealing_chance = 0.005
        self.steal_percentage = 0.1  # 5%

        self.fast_stealing_chance = 0.1
        self.fast_steal_abs_size = 1

        self.old_tick_time = time()
        self.tick = 0.02  # sec

        self.last_normal_snake_move_time = time()
        self.last_fast_snake_move_time = time()

        self.logging_level = logging_level
        self.setup_logger(__name__, "server/server.log", getattr(logging, self.logging_level))
        self.logger.info(f"Logging level: {self.logging_level}")

        self.base_viewport_width = BASE_VIEWPORT_WIDTH  # базовая ширина области видимости
        self.base_viewport_height = BASE_VIEWPORT_HEIGHT  # базовая высота области видимости
        self.viewport_scale_factor = 1  # увеличение области видимости для запаса

        # Кэш для оптимизации
        self.spatial_grid = {}  # Пространственное разбиение для быстрого поиска
        self.grid_cell_size = 1  # Размер ячейки сетки

        # TPS tracking
        self.tps_counter = 0
        self.last_tps_time = time()
        self.tps = 0
        self.tps_log_interval = 3  # Log TPS every 5 seconds


        # Кэш для оптимизации
        self._food_dict_cache = {}  # Кэш преобразования еды в dict
        self._snake_dict_cache = {}  # Кэш преобразования змей в dict
        self._last_cache_update = 0
        self.cache_ttl = 0.1  # Обновлять кэш каждые 100мс

    def get_color_for_segment(self, snake, segment_n):
        n = segment_n
        color = snake.color
        head = color.get("head")
        body = color.get("body")

        if type(body) == list:
            if segment_n == 0 and (not head is None):
                color_str = head
            else:
                if head is None:
                    index = (segment_n) % len(body)
                else:
                    index = (segment_n - 1) % len(body)

                color_str = body[index]

        else:
            raise ValueError(
                f"Snake color must be a str or list, but is is {repr(snake['color'])} with type {type(snake['color'])}")

        out_color = color_str
        if out_color is None:
            self.logger.warning(f"Unknown color: {color_str}; snake color: {snake['color']} ")
            out_color = "white"

        return out_color

    # def get_viewport_for_snake(self, snake: Snake) -> Viewport:
    #     """Улучшенная версия с динамическим масштабированием"""
    #     if not snake.body:
    #         return Viewport(0, 0, self.base_viewport_width, self.base_viewport_height)
    #
    #     head = snake.body[0]
    #
    #     # Динамическое масштабирование в зависимости от размера змеи
    #     size_factor = 1.0
    #     if self.viewport_settings['dynamic_scaling']:
    #         size_factor = max(1.0, min(2.0, 1.0 + len(snake.body) / 50))
    #
    #     viewport_width = int(self.viewport_settings['base_width'] *
    #                          self.viewport_settings['scale_factor'] * size_factor)
    #     viewport_height = int(self.viewport_settings['base_height'] *
    #                           self.viewport_settings['scale_factor'] * size_factor)
    #
    #     # Ограничение размеров
    #     viewport_width = max(self.viewport_settings['min_width'],
    #                          min(self.viewport_settings['max_width'], viewport_width))
    #     viewport_height = max(self.viewport_settings['min_height'],
    #                           min(self.viewport_settings['max_height'], viewport_height))
    #
    #     return Viewport(head.x, head.y, viewport_width, viewport_height)

    def update_spatial_grid(self):
        """Обновляет пространственное разбиение для оптимизации поиска"""
        self.spatial_grid = {}

        # Добавляем еду в сетку
        for food in self.food:
            cell_x = food.point.x // self.grid_cell_size
            cell_y = food.point.y // self.grid_cell_size
            cell_key = (cell_x, cell_y)
            if cell_key not in self.spatial_grid:
                self.spatial_grid[cell_key] = {'food': [], 'snake_ids': []}
            self.spatial_grid[cell_key]['food'].append(food)

        # Добавляем змей в сетку (по player_id)
        for player_id, snake in self.snakes.items():
            for segment in snake.body:
                cell_x = segment.x // self.grid_cell_size
                cell_y = segment.y // self.grid_cell_size
                cell_key = (cell_x, cell_y)
                if cell_key not in self.spatial_grid:
                    self.spatial_grid[cell_key] = {'food': [], 'snake_ids': []}
                if player_id not in self.spatial_grid[cell_key]['snake_ids']:
                    self.spatial_grid[cell_key]['snake_ids'].append(player_id)

    def get_viewport_for_snake(self, snake: Snake) -> Viewport:
        """Возвращает область видимости для змеи"""
        if not snake.body:
            return Viewport(0, 0, self.base_viewport_width, self.base_viewport_height)

        head = snake.body[0]
        viewport_width = int(self.base_viewport_width * self.viewport_scale_factor)
        viewport_height = int(self.base_viewport_height * self.viewport_scale_factor)

        return Viewport(head.x, head.y, viewport_width, viewport_height)

    def get_objects_in_viewport(self, viewport: Viewport):
        """Оптимизированная версия с предварительной фильтрацией ячеек"""
        visible_food = []
        visible_snake_ids = set()

        # Быстро вычисляем диапазон ячеек
        start_cell_x = max(-self.width // 2, viewport.left) // self.grid_cell_size
        end_cell_x = min(self.width // 2, viewport.right) // self.grid_cell_size
        start_cell_y = max(-self.height // 2, viewport.top) // self.grid_cell_size
        end_cell_y = min(self.height // 2, viewport.bottom) // self.grid_cell_size

        # Быстрая проверка только нужных ячеек
        for cell_x in range(int(start_cell_x), int(end_cell_x) + 1):
            for cell_y in range(int(start_cell_y), int(end_cell_y) + 1):
                cell_key = (cell_x, cell_y)
                if cell_key in self.spatial_grid:
                    cell_data = self.spatial_grid[cell_key]

                    # Быстрая проверка еды
                    for food in cell_data.get('food', []):
                        if (viewport.left <= food.point.x <= viewport.right and
                                viewport.top <= food.point.y <= viewport.bottom):
                            visible_food.append(food)

                    # Быстрая проверка змей
                    for player_id in cell_data.get('snake_ids', []):
                        if player_id not in visible_snake_ids:
                            snake = self.snakes.get(player_id)
                            if snake and self._snake_intersects_viewport_fast(snake, viewport):
                                visible_snake_ids.add(player_id)

        return list(visible_snake_ids), visible_food

    def _snake_intersects_viewport_fast(self, snake: Snake, viewport: Viewport) -> bool:
        """Быстрая проверка пересечения змеи с viewport"""
        # Проверяем только голову и хвост для экономии
        head = snake.body[0]
        if viewport.contains_point(head):
            return True

        tail = snake.body[-1]
        if viewport.contains_point(tail):
            return True

        # Если голова и хвост не видны, проверяем среднюю точку
        if len(snake.body) > 2:
            middle_idx = len(snake.body) // 2
            middle = snake.body[middle_idx]
            if viewport.contains_point(middle):
                return True

        return False
    async def set_server_desc(self, server_desc):
        self.server_desc = server_desc
        await self.broadcast_chat_message({"type": "set_server_desc",
                                           "data": self.server_desc})

    def setup_logger(self, name, log_file, level=logging.INFO):
        """Настройка логгера с выводом в консоль и файл."""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_formatter = logging.Formatter('[%(levelname)s] %(message)s')

        # Обработчик для записи в файл
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
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
                                           "data": f"<yellow>[</yellow><green>+</green><yellow>]</yellow> {await self.get_stilizate_name_color(player_id)} <yellow>joined the game</yellow>"})
        self.logger.info(
            f"Connection {self.get_addres_from_ws(self.connections[player_id])} registred as {self.get_player(player_id)}")
        return True

    async def remove_player(self, player_id):
        if player_id not in self.players.keys():
            return True
        self.logger.info(f"Player {self.get_player(player_id)} disconnected")
        del self.connections[player_id]
        await self.broadcast_chat_message({"type": "chat_message", "subtype": "join/left",
                                           "data": f"<yellow>[</yellow><red>-</red><yellow>]</yellow> {await self.get_stilizate_name_color(player_id)} <yellow>left the game</yellow>"})

        if player_id in self.snakes:
            del self.snakes[player_id]
        if player_id in self.players:
            del self.players[player_id]
        return True

    def change_direction(self, player_id, direction):
        if player_id in self.snakes:
            snake = self.snakes[player_id]

            if (direction == 'up' and snake.direction != 'down' and snake.next_direction != 'down') or \
                    (direction == 'down' and snake.direction != 'up' and snake.next_direction != 'up') or \
                    (direction == 'left' and snake.direction != 'right' and snake.next_direction != 'right') or \
                    (direction == 'right' and snake.direction != 'left' and snake.next_direction != 'left'):
                snake.next_direction = direction

    def add_random_food(self):

        x1, y1, x2, y2 = self.get_map_rect()
        x = random.randint(x1, x2)
        y = random.randint(y1, y2)
        self.add_food(x, y)
    def add_food(self, x, y, type_="default", color="red", size=1):
        self.food.append(Food(Point(x, y), type_=type_, color=color, size=size))
        # self.logger.debug(f"new food object at {x}, {y}")

    def generate_food(self):
        if self.get_all_food_count() < self.max_food:

            if len(self.food) < self.max_food:
                self.add_random_food()



    def get_player(self, player_id):

        try:
            address = "@" + self.get_addres_from_ws(self.connections[player_id])
        except KeyError:
            address = ""
        return f"{self.players[player_id].name}{address}"

    async def player_death(self, player_id, reason: str = "No reason", if_immortal=False):
        if self.snakes[player_id].immortal and not if_immortal:
            return False
        if not self.snakes[player_id].alive:
            raise ValueError(f"Snake {player_id} is already death!")
        sn = self.snakes[player_id]
        pl = self.players[player_id]
        self.snakes[player_id].alive = False
        body = self.snakes[player_id].body

        # del self.snakes[player_id]
        self.players[player_id].alive = False
        self.players[player_id].deaths += 1

        # state = self.to_dict()
        # ws = self.connections[player_id]
        # await ws.send(json.dumps(state))

        text = f'{reason.replace("%NAME%", await self.get_stilizate_name_color(player_id))}'
        self.logger.info(f"Player {self.get_player(player_id)} death ({text})")

        await self.connections[player_id].send(json.dumps({"type": "you_died", "data": text, "stats": {"size": sn.size,
                                                                                                       "max_size": sn.max_size,
                                                                                                       "deaths": pl.deaths,
                                                                                                       "kills": pl.kills}}))
        await self.broadcast_chat_message({"type": "chat_message", "subtype": "death_message",
                                           "data": text, "player_id": player_id})
        for n, i in enumerate(body):
            self.add_food(i.x, i.y, type_="death", color=self.get_color_for_segment(sn, n))

        return True

    def get_map_rect(self):
        x1, y1, x2, y2 = -(self.width // 2), -(self.height // 2), self.width // 2, self.height // 2
        return x1, y1, x2, y2

    def get_all_player_names(self):
        lst = []
        for k, v in self.players.items():
            lst.append(v.name)
        return lst

    def is_name_valid(self, name: str):
        if len(name) > 16:
            return f'Name "{name}" is too long'
        elif len(name) < 4:
            return f'Name "{name}" is too short'

        for i in name:
            if i.lower() not in self.VALID_NAME_CHARS:
                return f'Name "{name}" contain invalid characters'

        if name.lower() in [i.lower() for i in self.get_all_player_names()]:
            return f'Name "{name}" already in use'

        return True

    async def update_snake(self, player_id, snake):
        if not snake.alive:
            return

        should_move = (snake.is_fast and self.move_fast) or (not snake.is_fast and self.move_normal)
        if not should_move:
            return

        snake.direction = snake.next_direction
        head = snake.body[0]
        new_head = Point(head.x, head.y)

        # Используем словарь вместо if-else
        direction_offsets = {'up': (0, -1), 'down': (0, 1), 'left': (-1, 0), 'right': (1, 0)}
        dx, dy = direction_offsets[snake.direction]
        new_head.x += dx
        new_head.y += dy

        # Быстрая проверка стен
        walls = self.get_map_rect()  # Используем кэш
        if not (walls[0] <= new_head.x <= walls[2] and walls[1] <= new_head.y <= walls[3]):
            await self.player_death(player_id, "%NAME% crashed into the border")
            return

        # Оптимизированная проверка коллизий с использованием spatial grid
        head_cell_x = new_head.x // self.grid_cell_size
        head_cell_y = new_head.y // self.grid_cell_size
        head_cell_key = (head_cell_x, head_cell_y)

        # Проверка коллизий с другими змеями
        if head_cell_key in self.spatial_grid:
            for other_id in self.spatial_grid[head_cell_key].get('snake_ids', []):
                if other_id == player_id:
                    continue
                other_snake = self.snakes[other_id]
                if other_snake.alive and new_head in other_snake.body:
                    await self.player_death(player_id, f'%NAME% crashed into {other_snake.name}')
                    self.players[other_id].kills += 1
                    return

        # Проверка коллизий с собой (только первые N сегментов)
        max_self_check = len(snake.body)  # Проверяем только первые 10 сегментов
        for i, segment in enumerate(list(snake.body)[1:1 + max_self_check]):
            if new_head.x == segment.x and new_head.y == segment.y:
                await self.player_death(player_id, f'%NAME% crashed into his tail')
                return

        # Проверка еды через spatial grid
        food_eaten = False
        if head_cell_key in self.spatial_grid:
            for i, food in enumerate(self.spatial_grid[head_cell_key].get('food', [])):
                if new_head.x == food.point.x and new_head.y == food.point.y:
                    # Нашли еду - удаляем и выходим
                    self.food.remove(food)
                    snake.add_segment()
                    food_eaten = True
                    break

        # Move snake
        snake.body.appendleft(new_head)
        if not food_eaten:  # Удаляем хвост только если не съели еду
            snake.remove_segment()

    async def is_move_now(self, now):

        move_normal = now >= self.last_normal_snake_move_time + self.DEFAULT_MOVE_TIMEOUT
        move_fast = now >= self.last_fast_snake_move_time + self.FAST_MOVE_TIMEOUT
        return move_normal, move_fast

    async def update(self):
        self.generate_food()
        now = time()

        self.move_normal, self.move_fast = await self.is_move_now(now)
        if not (self.move_normal or self.move_fast):
            return

        # Update movement timers
        if self.move_normal:
            self.last_normal_snake_move_time = now
        if self.move_fast:
            self.last_fast_snake_move_time = now

        for player_id, snake in list(copy.copy(self.snakes).items()):
            try:
                await self.update_snake(player_id, snake)
            except Exception as e:
                self.logger.error("Error in updating snakes (update):")
                self.logger.exception(e)

        self.update_spatial_grid()

    def to_dict(self, player_id: str = None):
        return self._get_partial_state(player_id)

    def _get_full_state(self):
        """Полное состояние игры (существующая логика)"""
        dict_ = {
            'type': "game_state",
            'map_borders': [i for i in self.get_map_rect()],
            "snakes": {},
            "players": {},
            "food": [],
            "is_partial": False  # Флаг полного состояния
        }

        return dict_

    def _get_partial_state(self, player_id: str):
        """Оптимизированная версия с кэшированием"""
        if player_id not in self.snakes:
            return self._get_full_state()

        snake = self.snakes[player_id]
        viewport = self.get_viewport_for_snake(snake)
        visible_snake_ids, visible_food = self.get_objects_in_viewport(viewport)

        # Обновляем кэш если нужно
        current_time = time()
        if current_time - self._last_cache_update > self.cache_ttl:
            self._update_caches()
            self._last_cache_update = current_time

        dict_ = {
            'type': "game_state",
            'map_borders': self._cached_map_borders,  # Кэшированные границы
            "snakes": {},
            "players": {},
            "food": [],
            "viewport": {
                'center_x': viewport.center_x,
                'center_y': viewport.center_y,
                'width': viewport.width,
                'height': viewport.height
            },
            "is_partial": True
        }

        # Используем кэш для змей
        for visible_snake_id in visible_snake_ids:
            if visible_snake_id in self._snake_dict_cache:
                dict_["snakes"][visible_snake_id] = self._snake_dict_cache[visible_snake_id]

        if player_id not in dict_["snakes"] and player_id in self._snake_dict_cache:
            dict_["snakes"][player_id] = self._snake_dict_cache[player_id]

        # Используем кэш для еды
        for food in visible_food:
            food_key = (food.point.x, food.point.y, food.color)
            if food_key in self._food_dict_cache:
                dict_['food'].append(self._food_dict_cache[food_key])

        # Игроки
        for pid, pl in self.players.items():
            dict_['players'][pid] = self._player_to_dict(pl)

        return dict_

    def _update_caches(self):
        """Обновление кэшей"""
        # Кэш границ карты
        self._cached_map_borders = list(self.get_map_rect())

        # Кэш змей
        self._snake_dict_cache = {}
        for player_id, snake in self.snakes.items():
            self._snake_dict_cache[player_id] = self._snake_to_dict(snake)

        # Кэш еды
        self._food_dict_cache = {}
        for food in self.food:
            food_key = (food.point.x, food.point.y, food.color)
            self._food_dict_cache[food_key] = self._food_snake_to_dict(food)

    def _snake_to_dict(self, snake: Snake):
        return {
            'body': [{'x': p.x, "y": p.y} for p in snake.body],
            'color': snake.color,
            'name': snake.name,
            'size': snake.size,
            'max_size': snake.max_size,
            'alive': snake.alive,
            'direction': snake.direction,
            'is_fast': snake.is_fast
        }
    def _food_snake_to_dict(self, food: Food):
        return {
            'x': food.point.x,
            'y': food.point.y,
            'color': food.color,
            'type': food.type_,
        }

    def _player_to_dict(self, player: Player):
        """Конвертирует игрока в словарь"""
        return {
            "name": player.name,
            "color": player.color,
            "alive": player.alive,
            "kills": player.kills,
            "deaths": player.deaths
        }


    async def broadcast_chat_message(self, data):
        connections_ = copy.copy(self.connections)
        to_send = json.dumps(data)
        self.logger.debug(f"Broadcast data: {data}")

        for player_id, ws in connections_.items():

            try:
                await ws.send(to_send)
            except websockets.exceptions.ConnectionClosedOK as e:
                pass


    async def get_stilizate_name_color(self, player_id, text=None):
        color = self.players.get(player_id, {}).color
        if text == None:
            text = self.players.get(player_id).name

        if color in self.snake_colors:
            pass
        else:
            color = "white"

        return f"<{color}>{text}</{color}>"


    async def handle_client_chat_message(self, player_id, message: str):
        con = self.connections[player_id]

        if message.startswith("/"):
            self.logger.info(f"{self.get_player(player_id)} issued server command: {message}")
            lst = message.split()
            if lst[0] == "/help":
                await con.send(json.dumps({"type": "chat_message",
                                           "data": f"Help mesaage here?"}))
            elif lst[0] == "/kill":
                await self.player_death(player_id, "%NAME% committed suicide", if_immortal=True)
        else:
            self.logger.info(f"{self.get_player(player_id)} writes in chat: {message}")
            name = self.players[player_id].name
            await self.broadcast_chat_message(
                {"type": "chat_message", "data": f"{message}",
                 "from_user": f"{await self.get_stilizate_name_color(player_id)}"})


    async def handle_client_data(self, player_id: str, data: dict):
        self.logger.debug(f"Received data from {self.get_player(player_id)}: {data}")
        if data["type"] == "direction":

            self.change_direction(player_id, data['data'])
        elif data["type"] == "chat_message":
            await self.handle_client_chat_message(player_id, data["data"])
        # elif data["type"] == "kill_me":
        #     await self.player_death(player_id, "%NAME% committed suicide")
        elif data["type"] == "respawn":
            await self.respawn(player_id)
        elif data["type"] == "is_fast":
            await self.toggle_speed(player_id, data["data"])
        else:
            self.logger.warning(f"Unknown data type received from {self.get_player(player_id)}: {data}")

    async def toggle_speed(self, player_id, is_fast):
        self.logger.info(f"Snake {player_id} toggle is_fast: {is_fast}")
        pl = self.players[player_id]
        sn = self.snakes[player_id]
        if len(sn.body) < 2:
            return

        sn.is_fast = is_fast

    async def spawn(self, player_id, lenght=DEFAULT_SNAKE_LENGHT):
        x, y = self.get_avalible_coords()
        self.players[player_id].alive = True
        body = deque([Point(x, y)])
        direction = random.choice(DIRECTIONS)
        sn = self.snakes[player_id] = Snake(
            body=body,
            direction=direction,
            next_direction=direction,
            color=self.players[player_id].color,
            name=self.players[player_id].name,
            alive=True,

        )

        sn.add_segment(lenght)
        self.logger.info(f"Spawned {self.get_player(player_id)} ({self.players[player_id].name})")

        # self.players[player_id].alive = True


    async def respawn(self, player_id):
        await self.spawn(player_id)


    def get_pretty_address(self, websocket):
        if len(websocket.remote_address) == 2:
            return ":".join(str(i) for i in websocket.remote_address)
        else:
            return str(websocket.remote_address)


    def is_single_color_valid(self, color):
        if color in self.snake_colors:
            return True
        return False


    def is_color_valid(self, color):
        list_head_body = color.split(";", maxsplit=2)

        if len(list_head_body) == 2:
            head_str = list_head_body[0]
            body_str = list_head_body[1]
        elif len(list_head_body) == 1:
            head_str = None
            body_str = list_head_body[0]
        else:
            raise ValueError("Invalid head. Too many ';'")

        ls = body_str.split(",")

        if len(ls) > 20:
            raise ValueError("Color is too big")

        if (not head_str is None) and (not self.is_single_color_valid(head_str)):
            raise ValueError(f"Color head is invalid. Valid color options: {', '.join(self.snake_colors)}")

        for n, i in enumerate(ls):
            if not self.is_single_color_valid(i):
                raise ValueError(f"Color option № {n + 1} is invalid. Valid color options: {', '.join(self.snake_colors)}")

        out = {"body": ls}
        if not head_str is None:
            out["head"] = head_str
            out["name_color"] = "white"
        return out


    async def handle_connection(self, websocket):
        if len(self.players) >= self.max_players:
            self.logger.info(f"{self.get_pretty_address(websocket)} is trying to connect, but the server is full")
            await websocket.send(json.dumps({"type": "connection_error",
                                             "data": f"Server is full ({len(self.players)} / {self.max_players})"}))
            return
        else:
            self.logger.debug(f"{self.get_pretty_address(websocket)} is trying to connect to the server")
        while True:
            player_id = get_random_id()
            if not (player_id in self.players.keys()):
                self.logger.debug(f"{self.get_pretty_address(websocket)}`s player_id={player_id}")
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
                    self.logger.debug(f"{websocket.remote_address} choosen invalid name")
                    await websocket.send(json.dumps({"type": "connection_error",
                                                     "data": f"Invalid name: {name_valid}"}))
                    return

                color_str = player_info.get('color', None)
                try:
                    color = self.is_color_valid(color_str)

                except ValueError as e:
                    self.logger.debug(f"{websocket.remote_address} choosen invalid color: {e}")
                    await websocket.send(json.dumps({"type": "connection_error",
                                                     "data": f"Invalid snake color '{color_str}'\n{e}"}))
                    return

                await self.add_player(player_id, name, color)
                await websocket.send(json.dumps({"type": "set_server_desc", "data": self.server_desc}))

                async for message in websocket:
                    try:
                        data = json.loads(message)
                        await self.handle_client_data(player_id, data)
                    except Exception as e:
                        self.logger.error("Error while handle_client_data:")
                        self.logger.exception(e)

            except (json.JSONDecodeError, websockets.exceptions.ConnectionClosedError,
                    websockets.exceptions.ConnectionClosedOK) as e:
                self.logger.warning(f"{type(e).__name__}: {e}")
                await websocket.close()
                return
        except Exception as e:
            self.logger.error(f"Error while hanling connection {websocket}:")
            self.logger.exception(e)

        finally:

            await self.remove_player(player_id)
            await websocket.close()


    async def sometimes_steal_body(self, player_id):
        snake = self.snakes[player_id]
        if not snake.alive:
            return
        if random.random() < self.stealing_chance:
            current_length = len(snake.body)
            if current_length > self.min_steling_snake_size:
                segments_to_remove = max(1, int(current_length * self.steal_percentage))
                self.logger.debug(
                    f"Stole {segments_to_remove} segments ({self.steal_percentage * 100}%) from {self.get_player(player_id)}")

                snake.remove_segment(segments_to_remove, min_pop_size=self.min_steling_snake_size)
    async def fast_snake_steal_body(self, player_id):

        snake = self.snakes[player_id]

        # Проверяем, что змейка жива и является быстрой
        if not snake.alive or not snake.is_fast:
            return

        if random.random() < self.fast_stealing_chance:
            current_length = len(snake.body)
            if current_length > self.min_steling_snake_size:
                segments_to_remove = max(1, int(self.fast_steal_abs_size))

                # Создаем еду для каждого украденного сегмента
                for i in range(segments_to_remove):
                    # Берем сегменты с конца (хвост)
                    segment_index = current_length - i - 1
                    if segment_index < 0:  # Защита от отрицательных индексов
                        break

                    # Получаем позицию и цвет сегмента
                    point = snake.body[segment_index]
                    color = self.get_color_for_segment(snake, segment_index)

                    # Создаем еду на месте сегмента
                    self.add_food(point.x, point.y, type_="default", color=color, size=1)

                self.logger.debug(
                    f"FAST SPEEDStole {segments_to_remove} segments ({self.steal_percentage * 100}%) from {self.get_player(player_id)}")

                # Удаляем сегменты из тела змейки
                snake.remove_segment(segments_to_remove, min_pop_size=self.min_steling_snake_size)

    async def on_tick(self):

        await self.update()
        # TPS calculation
        self.tps_counter += 1
        current_time = time()
        if current_time - self.last_tps_time >= self.tps_log_interval:
            self.tps = self.tps_counter / (current_time - self.last_tps_time)
            self.tps_counter = 0
            self.last_tps_time = current_time
            self.logger.info(f"Server TPS: {self.tps:.2f}")

        for player_id, pl in self.players.items():
            pass
            await self.sometimes_steal_body(player_id)
            await self.fast_snake_steal_body(player_id)

        await self.send_game_state_to_all()

    async def send_game_state_to_all(self):
        """Отправляет состояние игры каждому клиенту с фильтрацией по области видимости"""
        try:
            # Обновляем пространственное разбиение


            connections_ = copy.copy(self.connections)
            for player_id, ws in connections_.items():
                try:
                    # Отправляем частичное состояние для каждого игрока
                    state = self.to_dict(player_id)
                    # self.logger.info("send state")
                    await ws.send(json.dumps(state))
                except websockets.exceptions.ConnectionClosedOK:
                    pass
        except Exception as e:
            self.logger.error("Error in send_game_state_to_all:")
            self.logger.exception(e)


    async def game_loop(self):
        try:
            while True:
                # if random.random() < 0.01:
                #     self.logger.info("ITER game_loop")

                now = time()

                if now >= self.old_tick_time + self.tick:
                    self.old_tick_time = now
                    await self.on_tick()

                    # # Optional: Warn if TPS is too low
                    # if hasattr(self, 'tps') and self.tps < 20 and self.tps > 0:
                    #     self.logger.warning(f"Low TPS: {self.tps:.2f}")

                await asyncio.sleep(self.game_speed)
        except Exception as e:
            self.logger.exception(e)
        finally:
            self.logger.info("game_loop closed")


    async def run(self):
        self.game_task = asyncio.create_task(self.game_loop())
        try:
            async with websockets.serve(self.handle_connection, self.address, self.port):
                print(f"Server started at {self.address}:{self.port}")
                await asyncio.Future()

        except Exception as e:
            self.logger.exception(e)
            self.logger.critical(f"SERVER CRASHED. Error: {type(e).__name__}: {e}")

        finally:
            self.logger.debug("Canceling main loop task...")
            self.game_task.cancel()
            try:
                await self.game_task
            except KeyboardInterrupt:
                pass


def get_random_id():
    return hex(random.randint(0, 131_072))


def positive_int(value):
    val = int(value)
    if val <= 0:
        raise argparse.ArgumentTypeError(f"{value} is not a positive integer")
    return val


async def run_server():
    parser = argparse.ArgumentParser(description="Multiplayer Snake game by @Arizel79 (server)")
    parser.add_argument('--address', "--ip", type=str, help='Server address (default: 0.0.0.0)', default="0.0.0.0")
    parser.add_argument('--port', "--p", type=int, help='Server port (default: 8090)', default=8090)
    parser.add_argument('--server_name', type=str, help='Server name', default="Snake Server")
    parser.add_argument('--server_desc', type=str, help='Description of server', default="This is server")
    parser.add_argument('--max_players', type=positive_int, help='Max online players count', default=20)
    parser.add_argument('--map_width', "--width", "--w", "--x_size", type=int, help='Width of server map', default=100)
    parser.add_argument('--map_height', "--height", "--h", "--y_size", type=int, help='Height of server map',
                        default=100)
    parser.add_argument('--food_perc', type=int, help='Proportion food/map in perc', default=4)
    parser.add_argument('--default_move_timeout', '--default_move', type=float, help='Timeout move snake (sec)',
                        default=0.1)
    parser.add_argument('--fast_move_timeout', '--fast_move', type=float, help='Timeout move fast snake (sec)',
                        default=0.1)
    parser.add_argument('--logging_level', '--log_lvl', type=str,
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Level of logging', default="INFO")
    args = parser.parse_args()

    game_state = Server(address=args.address, port=args.port, map_width=args.map_width, map_height=args.map_height,
                        max_players=args.max_players, server_name=args.server_name, server_desc=args.server_desc,
                        logging_level=args.logging_level, max_food_perc=args.food_perc,
                        default_move_timeout=args.default_move_timeout, fast_move_timeout=args.fast_move_timeout)
    try:
        await game_state.run()
    except asyncio.CancelledError:
        pass  # Игнорируем CancelledError при нормальном завершении
    finally:
        print("Server finished")


def main():
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt. Server quit")
        return


if __name__ == '__main__':
    main()
