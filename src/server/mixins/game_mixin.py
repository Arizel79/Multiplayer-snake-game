import asyncio
import copy

from src.server.mixins.base_mixin import BaseMixin
from time import time


class GameMixin(BaseMixin):
    async def game_loop(self):
        try:
            self.logger.info(
                f"Server game_loop started (TPS limit: {self.config.tps_limit})"
            )

            tick_interval = 1.0 / self.config.tps_limit
            next_tick = time() + tick_interval

            while True:
                try:
                    current_time = time()

                    sleep_time = next_tick - current_time
                    if sleep_time > 0:
                        await asyncio.sleep(sleep_time)

                    next_tick = max(next_tick + tick_interval, time() + tick_interval)

                    await self.on_tick()

                except Exception as e:
                    self.logger.error(f"Error in game_loop: {e}")
                    self.logger.exception(e)
                    await asyncio.sleep(0)

        except asyncio.CancelledError:
            self.logger.debug("CancelledError in game_loop")
        except Exception as e:
            self.logger.error("Game loop error:")
            self.logger.exception(e)
        finally:
            self.logger.info("Server game_loop closed")

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
