from time import time

from src.server.mixins.base_mixin import BaseMixin
from src.server.modules.config import LOW_TPS


class UpdatesMixin(BaseMixin):
    async def on_tick(self):
        await self.update()

        self.tps_counter += 1
        current_time = time()
        if current_time - self.last_tps_time >= self.config.tps_log_interval:
            self.tps = self.tps_counter / (current_time - self.last_tps_time)
            self.tps_counter = 0
            self.last_tps_time = current_time

            if abs(self.tps - self.config.tps_limit) > self.config.tps_limit * 0.5:
                self.logger.info(f"Server TPS: {self.tps:.2f} (target: {self.config.tps_limit})")

        for player_id, pl in self.players.items():
            if pl.is_frozen:
                continue

            await self.sometimes_steal_body(player_id)
            await self.fast_snake_steal_body(player_id)

        await self.send_game_state_to_all()
