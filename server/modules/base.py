import asyncio

import websockets

from server.mixins.chat_handler_mixin import ChatHandlerMixin
from server.mixins.communication_mixin import CommunicationMixin
from server.mixins.game_mixin import GameMixin
from server.mixins.handle_connection_mixin import HandleConnectionMixin
from server.mixins.players_mixin import PlayersMixin
from server.mixins.send_game_state_mixin import SendGameStateMixin
from server.mixins.snakes_mixin import SnakesMixin
from server.mixins.updates_mixin import UpdatesMixin
from server.mixins.utils_mixin import UtilsMixin
from server.mixins.viewport_mixin import ViewportMixin


class BaseServer(
    ChatHandlerMixin,
    UtilsMixin,
    ViewportMixin,
    CommunicationMixin,
    PlayersMixin,
    SnakesMixin,
    SendGameStateMixin,
    UpdatesMixin,
    HandleConnectionMixin,
    GameMixin,
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.game_task = None

    async def run(self):
        self.game_task = asyncio.create_task(self.game_loop())
        try:
            async with websockets.serve(
                self.handle_connection, self.config.address, self.config.port
            ):
                self.logger.info(
                    f"Server started at {self.config.address}:{self.config.port}"
                )
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
