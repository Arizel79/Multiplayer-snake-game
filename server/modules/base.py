import asyncio
import json
from time import time

import websockets

from server.mixins.chat_handler_mixin import ChatHandlerMixin
from server.mixins.communication_mixin import CommunicationMixin
from server.mixins.handle_connection_mixin import HandleConnectionMixin
from server.mixins.players_mixin import PlayersMixin
from server.mixins.send_game_state_mixin import SendGameStateMixin
from server.mixins.snakes_mixin import SnakesMixin
from server.mixins.updates_mixin import UpdatesMixin
from server.mixins.utils_mixin import UtilsMixin
from server.mixins.viewport_mixin import ViewportMixin
from server.modules.dataclasses import *
from server.utils import get_random_id


class BaseServer(
    ChatHandlerMixin,
    UtilsMixin,
    ViewportMixin,
    CommunicationMixin,
    PlayersMixin,
    SnakesMixin,
    SendGameStateMixin,
    UpdatesMixin,
    HandleConnectionMixin
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
