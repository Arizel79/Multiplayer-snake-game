import asyncio

import websockets

from src.server.mixins.chat_handler_mixin import ChatHandlerMixin
from src.server.mixins.communication_mixin import CommunicationMixin
from src.server.mixins.game_mixin import GameMixin
from src.server.mixins.handle_connection_mixin import HandleConnectionMixin
from src.server.mixins.main_mixin import MainMixin
from src.server.mixins.players_mixin import PlayersMixin
from src.server.mixins.send_game_state_mixin import SendGameStateMixin
from src.server.mixins.snakes_mixin import SnakesMixin
from src.server.mixins.updates_mixin import UpdatesMixin
from src.server.mixins.utils_mixin import UtilsMixin
from src.server.mixins.viewport_mixin import ViewportMixin


class Server(
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
    MainMixin,
):
    pass
