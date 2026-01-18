import copy
import json

import websockets

from server.mixins.base_mixin import BaseMixin


class CommunicationMixin(BaseMixin):
    def get_addres_from_ws(self, ws):
        return ":".join(str(i) for i in ws.remote_address)

    async def send_dict_to_player(self, player_id, dict_):
        await self.send_dict_to_ws(self.connections[player_id], dict_)

    async def send_dict_to_ws(self, ws, dict_):
        try:
            assert isinstance(dict_, dict), f"dict_ is not a dict: {repr(dict_)}"
            assert dict_.get("type")

            to_send = json.dumps(dict_)
            await ws.send(to_send)
        except Exception as e:
            self.logger.debug(f"Error send to websocket {ws} {type(e).__name__}: {e}")
            await ws.close()

    async def broadcast_chat_message(self, data):
        connections_ = copy.copy(self.connections)

        self.logger.info(f"Broadcast data: {data}")

        for player_id, ws in connections_.items():
            await self.send_dict_to_ws(ws, data)

    async def handle_client_data(self, player_id: str, data: dict):
        try:
            self.logger.debug(
                f"Received data from {self.get_player(player_id)}: {data}"
            )
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

        except KeyError as e:
            self.logger.debug(f"KeyError: {e}")

    async def send_game_state_to_all(self):
        try:
            connections_ = copy.copy(self.connections)
            for player_id, ws in connections_.items():
                try:

                    state_to_send = self.to_dict(player_id)
                    if not state_to_send:
                        continue
                    if self._send_cache_for_players.get(player_id) != state_to_send:
                        await self.send_dict_to_ws(ws, state_to_send)
                        self._send_cache_for_players[player_id] = state_to_send

                except websockets.exceptions.ConnectionClosedOK:
                    pass
        except Exception as e:
            self.logger.error(f"Error in send_game_state_to_all: {e}")
            self.logger.exception(e)
