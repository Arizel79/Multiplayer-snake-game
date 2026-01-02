import asyncio

import websockets

from server.mixins.chat_handler_mixin import ChatHandlerMixin
from server.mixins.communication_mixin import CommunicationMixin
from server.mixins.game_mixin import GameMixin
from server.mixins.handle_connection_mixin import HandleConnectionMixin
from server.mixins.main_mixin import MainMixin
from server.mixins.players_mixin import PlayersMixin
from server.mixins.send_game_state_mixin import SendGameStateMixin
from server.mixins.snakes_mixin import SnakesMixin
from server.mixins.updates_mixin import UpdatesMixin
from server.mixins.utils_mixin import UtilsMixin
from server.mixins.viewport_mixin import ViewportMixin


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
    MainMixin
):
   pass