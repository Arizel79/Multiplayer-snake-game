import logging
import random
import sys

from src.server.mixins.base_mixin import BaseMixin
from src.server.modules.config import *
from src.server.modules.dataclasses import *


class UtilsMixin(BaseMixin):
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
                f"Snake color must be a str or list, but is is {repr(snake['color'])} with type {type(snake['color'])}"
            )

        out_color = color_str
        if out_color is None:
            self.logger.warning(
                f"Unknown color: {color_str}; snake color: {snake['color']} "
            )
            out_color = "white"

        return out_color

    async def set_server_desc(self, server_desc):
        self.server_desc = server_desc
        await self.broadcast_chat_message(
            {"type": "set_server_desc", "data": self.server_desc}
        )

    def get_map_rect(self):
        x1, y1, x2, y2 = (
            -(self.config.width // 2),
            -(self.config.height // 2),
            self.config.width // 2,
            self.config.height // 2,
        )
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
            if i.lower() not in self.config.VALID_NAME_CHARS:
                return f'Name "{name}" contain invalid characters'

        if name.lower() in [i.lower() for i in self.get_all_player_names()]:
            return f'Name "{name}" already in use'

        return True

    def is_single_color_valid(self, color):
        if color in self.config.snake_colors:
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

        if len(ls) > 64:
            raise ValueError("Color is too big")

        if (not head_str is None) and (not self.is_single_color_valid(head_str)):
            raise ValueError(
                f"Color head is invalid. Valid color options: {', '.join(self.config.snake_colors)}"
            )

        if len(ls) > MAX_PLAYER_COLOR_LENGHT:
            raise ValueError(
                f"Color is too long: {len(ls)}, max: {MAX_PLAYER_COLOR_LENGHT}"
            )
        for n, i in enumerate(ls):
            if not self.is_single_color_valid(i):
                raise ValueError(
                    f"Color option № {n + 1} is invalid. Valid color options: {', '.join(self.config.snake_colors)}"
                )

        out = {"body": ls}
        if head_str:
            out["head"] = head_str
            out["name_color"] = head_str
        else:
            out["name_color"] = ls[0]

        assert out.get("name_color")
        return out

    def get_pretty_address(self, websocket):
        if len(websocket.remote_address) == 2:
            return ":".join(str(i) for i in websocket.remote_address)
        else:
            return str(websocket.remote_address)

    async def get_stilizate_name_color(self, player_id, text=None):
        color = self.players.get(player_id, {}).color
        if text == None:
            text = self.players.get(player_id).name

        if color in self.config.snake_colors:
            pass
        else:
            color = "white"

        return f"<{color}>{text}</{color}>"

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
            if not p in self.food.keys():
                break
        return x, y

    def add_random_food(self):
        x1, y1, x2, y2 = self.get_map_rect()
        x = random.randint(x1, x2)
        y = random.randint(y1, y2)
        self.add_food(x, y)

    def get_random_id(self):
        return hex(random.randint(0, 131_072))

    def add_food(
        self, x, y, type_=FOOD_TYPES.default, color=DEFAULT_FOOD_COLOR, size=1
    ):
        if self.food.get((x, y)):
            return
        self.food[(x, y)] = Food(Point(x, y), type_=type_, color=color, size=size)

    def generate_food(self):
        while self.get_all_food_count() < self.config.max_food:
            self.add_random_food()
