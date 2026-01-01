import copy
import json

import websockets

from server.mixins.base_mixin import BaseMixin


class CommunicationMixin(BaseMixin):
    def get_addres_from_ws(self, ws):
        return ":".join(str(i) for i in ws.remote_address)

    async def send_dict_to_player(self, player_id, dict_):
        try:
            await self.connections[player_id].send(json.dumps(dict_))
        except Exception as e:
            self.logger.error(f"Error send to {player_id}: {e}")

    async def broadcast_chat_message(self, data):
        connections_ = copy.copy(self.connections)
        to_send = json.dumps(data)
        self.logger.debug(f"Broadcast data: {data}")

        for player_id, ws in connections_.items():

            try:
                await ws.send(to_send)
            except websockets.exceptions.ConnectionClosedOK as e:
                pass

    async def handle_client_data(self, player_id: str, data: dict):
        self.logger.debug(f"Received data from {self.get_player(player_id)}: {data}")
        if data["type"] == "direction":

            self.change_direction(player_id, data["data"])
        elif data["type"] == "chat_message":
            await self.handle_client_chat_message(player_id, data["data"])
        elif data["type"] == "respawn":
            await self.respawn(player_id)
        elif data["type"] == "is_fast":
            await self.toggle_speed(player_id, data["data"])
        else:
            self.logger.warning(
                f"Unknown data type received from {self.get_player(player_id)}: {data}"
            )

    async def send_game_state_to_all(self):
        try:
            connections_ = copy.copy(self.connections)
            for player_id, ws in connections_.items():
                try:

                    state = self.to_dict(player_id)
                    if self._send_cache.get(player_id) != state:
                        await ws.send(json.dumps(state))
                        self._send_cache[player_id] = state

                    else:
                        pass
                except websockets.exceptions.ConnectionClosedOK:
                    pass
        except Exception as e:
            self.logger.error(f"Error in send_game_state_to_all: {e}")
