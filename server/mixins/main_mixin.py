from server.mixins.base_mixin import BaseMixin

import asyncio

import websockets
class MainMixin(BaseMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.game_task = None

    async def run(self):
        self.game_task = asyncio.create_task(self.game_loop())
        try:
            async with websockets.serve(
                    self.handle_connection, self.config.address, self.config.port,
                    ping_interval=20,  # отправлять ping каждые 20 секунд
                    ping_timeout=40  # ждать pong до 40 секунд
            ):
                self.logger.info(
                    f"Server started at {self.config.address}:{self.config.port}"
                )
                await asyncio.Future()

        except Exception as e:
            self.logger.error("Error in run():")
            self.logger.exception(e)
            self.logger.critical(f"Server crashed: {type(e).__name__}: {e}")

        finally:
            self.logger.debug("Canceling main loop task...")
            self.game_task.cancel()
            try:
                await self.game_task
            except KeyboardInterrupt:
                pass
