import asyncio
import json
from time import time

import websockets

from server.mixins.chat_handler_mixin import ChatHandlerMixin
from server.mixins.communication_mixin import CommunicationMixin
from server.mixins.players_mixin import PlayersMixin
from server.mixins.snakes_mixin import SnakesMixin
from server.mixins.utils_mixin import UtilsMixin
from server.mixins.viewport_mixin import ViewportMixin
from server.modules.dto import *
from server.utils import get_random_id


class BaseServer(
    ChatHandlerMixin,
    UtilsMixin,
    ViewportMixin,
    CommunicationMixin,
    PlayersMixin,
    SnakesMixin,
):

    async def update(self):
        self.generate_food()
        now = time()

        self.move_normal, self.move_fast = await self.is_move_now(now)
        if not (self.move_normal or self.move_fast):
            return

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

    async def handle_connection(self, websocket):
        try:
            try:
                player_id = None

                pl_count = len(self.connections)
                pl_count_max = self.max_players
                self.logger.info(
                    f"check max player for {self.get_pretty_address(websocket)}: {pl_count} >= {pl_count_max}"
                )

                if pl_count >= pl_count_max:

                    self.logger.info(
                        f"{self.get_pretty_address(websocket)} is trying to connect, but the server is full"
                    )
                    await websocket.send(
                        json.dumps(
                            {
                                "type": "connection_error",
                                "data": f"Server is full ({pl_count} / {pl_count_max})",
                            }
                        )
                    )
                    return
                else:
                    self.logger.info(
                        f"{self.get_pretty_address(websocket)} is trying to connect to the server"
                    )
                while True:
                    player_id = get_random_id()
                    if not (player_id in self.players.keys()):
                        self.logger.debug(
                            f"{self.get_pretty_address(websocket)}`s player_id={player_id}"
                        )
                        break
                self.connections[player_id] = websocket
                await websocket.send(
                    json.dumps({"player_id": player_id, "type": "player_id"})
                )

                try:
                    data = await websocket.recv()
                    player_info = json.loads(data)
                    name = player_info.get("name", "Player")
                    name_valid = self.is_name_valid(name)
                    if not name_valid is True:
                        self.logger.debug(
                            f"{websocket.remote_address} choose invalid name"
                        )
                        await websocket.send(
                            json.dumps(
                                {
                                    "type": "connection_error",
                                    "data": f"Invalid name: {name_valid}",
                                }
                            )
                        )
                        return

                    color_str = player_info.get("color", None)
                    try:
                        color = self.is_color_valid(color_str)

                    except ValueError as e:
                        self.logger.debug(
                            f"{websocket.remote_address} choose invalid color: {e}"
                        )
                        await websocket.send(
                            json.dumps(
                                {
                                    "type": "connection_error",
                                    "data": f"Invalid snake color '{color_str}'\n{e}",
                                }
                            )
                        )
                        return

                    await self.add_player(player_id, name, color)
                    await websocket.send(
                        json.dumps(
                            {"type": "set_server_desc", "data": self.server_desc}
                        )
                    )

                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            await self.handle_client_data(player_id, data)
                        except Exception as e:
                            self.logger.error("Error while handle_client_data:")
                            self.logger.exception(e)

                except (
                    json.JSONDecodeError,
                    websockets.exceptions.ConnectionClosedError,
                    websockets.exceptions.ConnectionClosedOK,
                    websockets.exceptions.InvalidMessage,
                ) as e:
                    self.logger.warning(f"{type(e).__name__}: {e}")
                    await websocket.close()
                    return

            except Exception as e:
                self.logger.error(f"Error while handling connection {websocket}:")
                self.logger.exception(e)

            finally:
                if player_id:
                    await self.remove_player(player_id)

                await websocket.close()
                self.logger.info("ws colsed fin")

        except Exception as e:
            self.logger.error("Unx")
            self.logger.exception(e)

    async def on_tick(self):
        await self.update()

        self.tps_counter += 1
        current_time = time()
        if current_time - self.last_tps_time >= self.tps_log_interval:
            self.tps = self.tps_counter / (current_time - self.last_tps_time)
            self.tps_counter = 0
            self.last_tps_time = current_time
            if self.tps < 14:
                self.logger.info(f"Server TPS (low): {self.tps:.1f}")

        for player_id, pl in self.players.items():
            await self.sometimes_steal_body(player_id)
            await self.fast_snake_steal_body(player_id)

        await self.send_game_state_to_all()

    async def game_loop(self):
        try:
            while True:
                now = time()

                if now >= self.old_tick_time + self.tick:
                    self.old_tick_time = now
                    await self.on_tick()

                    # Optional: Warn if TPS is too low
                    # if hasattr(self, 'tps') and self.tps < 20 and self.tps > 0:
                    #     self.logger.warning(f"Low TPS: {self.tps:.2f}")

                await asyncio.sleep(self.game_speed)
        except Exception as e:
            self.logger.error("Game loop error:")
            self.logger.exception(e)
        finally:
            self.logger.info("game_loop closed")

    async def run(self):
        self.game_task = asyncio.create_task(self.game_loop())
        try:
            async with websockets.serve(
                self.handle_connection, self.address, self.port
            ):
                self.logger.info(f"Server started at {self.address}:{self.port}")
                await asyncio.Future()

        except Exception as e:
            self.logger.error("Error (run):")
            self.logger.exception(e)
            self.logger.critical(f"SERVER CRASHED. Error: {type(e).__name__}: {e}")

        finally:
            self.logger.debug("Canceling main loop task...")
            self.game_task.cancel()
            try:
                await self.game_task
            except KeyboardInterrupt:
                pass
