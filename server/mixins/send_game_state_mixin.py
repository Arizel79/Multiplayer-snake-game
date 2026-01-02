from time import time

from server.mixins.base_mixin import BaseMixin
from server.modules.dataclasses import *


class SendGameStateMixin(BaseMixin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._leaderboard_cache = {}
        self._last_leaderboard_update = 0
        self.leaderboard_cache_ttl = 0.5

    def _get_leaderboard(self, limit=10):
        """Получение топа змеек по размеру"""
        current_time = time()

        # Обновляем кэш раз в leaderboard_cache_ttl секунд
        if current_time - self._last_leaderboard_update > self.leaderboard_cache_ttl:
            self._update_leaderboard_cache(limit)
            self._last_leaderboard_update = current_time

        return self._leaderboard_cache

    def _update_leaderboard_cache(self, limit=10):
        """Обновление кэша leaderboard"""

        snakes_data = []
        for player_id, snake in self.snakes.items():
            if snake.alive:
                player = self.players.get(player_id)

                if player:
                    snakes_data.append(
                        {
                            "id": player_id,
                            "name": player.name,
                            "score": snake.size,
                            "name_color": player.color["name_color"],
                        }
                    )

        snakes_data.sort(key=lambda x: x["score"], reverse=True)

        top_snakes = snakes_data[:limit]

        leaderboard = {}
        for i, snake_data in enumerate(top_snakes, 1):
            leaderboard[i] = {
                "name": snake_data["name"],
                "score": snake_data["score"],
                "name_color": snake_data["name_color"],
                "id": snake_data["id"],
            }

        self._leaderboard_cache = leaderboard

    def to_dict(self, player_id: str = None):
        state = self._get_partial_state(player_id)

        return state

    def _get_full_state(self):
        """Полное состояние игры (существующая логика)"""
        dict_ = {
            "type": "game_state",
            # "map_borders": [i for i in self.get_map_rect()],
            "snakes": {},
            "players": {},
            "food": [],
            "is_partial": False,
        }

        return dict_

    def _get_partial_state(self, player_id: str):
        """Оптимизированная версия с кэшированием"""
        if player_id not in self.snakes:
            self.logger.warning(f"{player_id} not in snakes")
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
            # "map_borders": self._cached_map_borders,
            "snakes": {},
            "players": {},
            "food": [],
            "viewport": {
                "center_x": viewport.center_x,
                "center_y": viewport.center_y,
                "width": viewport.width,
                "height": viewport.height,
            },
            "leaderboard": self._get_leaderboard(),
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

    def get_map_borders(self):
        return list(self.get_map_rect())

    def _update_caches(self):
        """Обновление кэшей"""
        self._cached_map_borders = self.get_map_borders

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
