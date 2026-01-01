import copy

from server.mixins.base_mixin import BaseMixin
from time import time


class GameMixin(BaseMixin):
    async def game_loop(self):
        try:
            self.logger.info("Server game_loop started")
            while True:
                try:
                    now = time()

                    if now >= self.old_tick_time + self.config.tick:
                        self.old_tick_time = now
                        await self.on_tick()

                    await asyncio.sleep(self.config.game_speed)
                except Exception as e:
                    self.logger.error(f"Error in game_loop: {e}")
                    self.logger.exception(e)
        except asyncio.CancelledError as e:
            self.logger.exception(e)
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
