import json

import websockets

from server.mixins.base_mixin import BaseMixin
from server.utils import get_random_id


class HandleConnectionMixin(BaseMixin):
    async def handle_connection(self, websocket):
        try:
            try:
                player_id = None

                pl_count = len(self.connections)
                pl_count_max = self.max_players
                self.logger.info(
                    f"check max player for {self.get_pretty_address(websocket)}: {pl_count} >= {pl_count_max}"
                )

                if pl_count >= pl_count_max:

                    self.logger.info(
                        f"{self.get_pretty_address(websocket)} is trying to connect, but the server is full"
                    )
                    await websocket.send(
                        json.dumps(
                            {
                                "type": "connection_error",
                                "data": f"Server is full ({pl_count} / {pl_count_max})",
                            }
                        )
                    )
                    return
                else:
                    self.logger.info(
                        f"{self.get_pretty_address(websocket)} is trying to connect to the server"
                    )
                while True:
                    player_id = get_random_id()
                    if not (player_id in self.players.keys()):
                        self.logger.debug(
                            f"{self.get_pretty_address(websocket)}`s player_id={player_id}"
                        )
                        break
                self.connections[player_id] = websocket
                await websocket.send(
                    json.dumps({"player_id": player_id, "type": "player_id"})
                )

                try:
                    data = await websocket.recv()
                    player_info = json.loads(data)
                    name = player_info.get("name", "Player")
                    name_valid = self.is_name_valid(name)
                    if not name_valid is True:
                        self.logger.debug(
                            f"{websocket.remote_address} choose invalid name"
                        )
                        await websocket.send(
                            json.dumps(
                                {
                                    "type": "connection_error",
                                    "data": f"Invalid name: {name_valid}",
                                }
                            )
                        )
                        return

                    color_str = player_info.get("color", None)
                    try:
                        color = self.is_color_valid(color_str)

                    except ValueError as e:
                        self.logger.debug(
                            f"{websocket.remote_address} choose invalid color: {e}"
                        )
                        await websocket.send(
                            json.dumps(
                                {
                                    "type": "connection_error",
                                    "data": f"Invalid snake color '{color_str}'\n{e}",
                                }
                            )
                        )
                        return

                    await self.add_player(player_id, name, color)
                    await websocket.send(
                        json.dumps(
                            {"type": "set_server_desc", "data": self.server_desc}
                        )
                    )

                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            await self.handle_client_data(player_id, data)
                        except Exception as e:
                            self.logger.error("Error while handle_client_data:")
                            self.logger.exception(e)

                except (
                        json.JSONDecodeError,
                        websockets.exceptions.ConnectionClosedError,
                        websockets.exceptions.ConnectionClosedOK,
                        websockets.exceptions.InvalidMessage,
                ) as e:
                    self.logger.warning(f"{type(e).__name__}: {e}")
                    await websocket.close()
                    return

            except Exception as e:
                self.logger.error(f"Error while handling connection {websocket}:")
                self.logger.exception(e)

            finally:
                if player_id:
                    await self.remove_player(player_id)

                await websocket.close()
                self.logger.debug("WS closed")

        except Exception as e:
            self.logger.error("Unx")
            self.logger.exception(e)
