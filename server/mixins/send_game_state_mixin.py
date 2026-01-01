from time import time

from server.mixins.base_mixin import BaseMixin
from server.modules.dataclasses import *


class SendGameStateMixin(BaseMixin):
    def to_dict(self, player_id: str = None):
        return self._get_partial_state(player_id)

    def _get_full_state(self):
        """Полное состояние игры (существующая логика)"""
        dict_ = {
            "type": "game_state",
            "map_borders": [i for i in self.get_map_rect()],
            "snakes": {},
            "players": {},
            "food": [],
            "is_partial": False,
        }

        return dict_

    def _get_partial_state(self, player_id: str):
        """Оптимизированная версия с кэшированием"""
        if player_id not in self.snakes:
            return self._get_full_state()

        snake = self.snakes[player_id]
        viewport = self.get_viewport_for_snake(snake)
        visible_snake_ids, visible_food = self.get_objects_in_viewport(viewport)

        current_time = time()
        if current_time - self._last_cache_update > self.cache_ttl:
            self._update_caches()
            self._last_cache_update = current_time

        dict_ = {
            "type": "game_state",
            "map_borders": self._cached_map_borders,
            "snakes": {},
            "players": {},
            "food": [],
            "viewport": {
                "center_x": viewport.center_x,
                "center_y": viewport.center_y,
                "width": viewport.width,
                "height": viewport.height,
            },
            "is_partial": True,
            "tps": round(self.tps, 1),
        }

        for visible_snake_id in visible_snake_ids:
            if visible_snake_id in self._snake_dict_cache:
                dict_["snakes"][visible_snake_id] = self._snake_dict_cache[
                    visible_snake_id
                ]

        if player_id not in dict_["snakes"] and player_id in self._snake_dict_cache:
            dict_["snakes"][player_id] = self._snake_dict_cache[player_id]

        for food in visible_food:
            food_key = (food.point.x, food.point.y, food.color)
            if food_key in self._food_dict_cache:
                dict_["food"].append(self._food_dict_cache[food_key])

        for pid, pl in self.players.items():
            dict_["players"][pid] = self._player_to_dict(pl)

        return dict_

    def _update_caches(self):
        """Обновление кэшей"""
        self._cached_map_borders = list(self.get_map_rect())

        self._snake_dict_cache = {}
        for player_id, snake in self.snakes.items():
            self._snake_dict_cache[player_id] = self._snake_to_dict(snake)

        self._food_dict_cache = {}
        for xy, food in self.food.items():
            food_key = (food.point.x, food.point.y, food.color)
            self._food_dict_cache[food_key] = self._food_snake_to_dict(food)

    def _food_snake_to_dict(self, food: Food):
        return {
            "x": food.point.x,
            "y": food.point.y,
            "color": food.color,
            "type": food.type_,
        }

    def _player_to_dict(self, player: Player):
        """Конвертирует игрока в словарь"""
        return {
            "name": player.name,
            "color": player.color,
            "alive": player.alive,
            "kills": player.kills,
            "deaths": player.deaths,
        }
