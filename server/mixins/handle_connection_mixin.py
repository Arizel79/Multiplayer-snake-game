import asyncio
import json

import websockets

from server.mixins.base_mixin import BaseMixin
from server.modules.config import TIMEOUT_WAIT_PLAYER_INFO
from server.utils import get_random_id


class HandleConnectionMixin(BaseMixin):

    async def handle_registration(self, ws):
        is_ok = False
        self.logger.info(f"registration {ws}...")
        player_id = None

        pl_count = len(self.connections)
        pl_count_max = self.config.max_players
        self.logger.debug(
            f"check max player for {self.get_pretty_address(ws)}: {pl_count} >= {pl_count_max}"
        )

        if pl_count >= pl_count_max:
            self.logger.info(
                f"{self.get_pretty_address(ws)} is trying to connect, but the server is full"
            )
            await self.send_dict_to_ws(
                ws,
                {
                    "type": "connection_error",
                    "data": f"Server is full ({pl_count} / {pl_count_max})",
                },
            )
            return
        else:
            self.logger.info(
                f"{self.get_pretty_address(ws)} is trying to connect to the server"
            )
        while True:
            player_id = get_random_id()
            if not (player_id in self.players.keys()):
                self.logger.debug(
                    f"{self.get_pretty_address(ws)}`s player_id={player_id}"
                )
                break
        self.connections[player_id] = ws
        await self.send_dict_to_ws(
            ws, {"player_id": player_id, "type": "player_id"}
        )

        try:

            try:
                data = await asyncio.wait_for(ws.recv(), timeout=TIMEOUT_WAIT_PLAYER_INFO)
            except asyncio.TimeoutError as e:
                self.logger.info(f"Wait player info timeout ({TIMEOUT_WAIT_PLAYER_INFO})")
                return
            player_info = json.loads(data)
            is_slyth_game = player_info.get("slyth_game", False)
            if not is_slyth_game:
                self.logger.info(f"In player_info no slyth_game: true")
                return
            name = player_info.get("name", "Player")
            name_valid = self.is_name_valid(name)
            if not name_valid is True:
                self.logger.debug(f"{self.get_pretty_address(ws)} choose invalid name")
                await self.send_dict_to_ws(
                    ws,
                    {
                        "type": "connection_error",
                        "data": f"Invalid name: {name_valid}",
                    },
                )
                return

            color_str = player_info.get("color", None)
            try:
                color = self.is_color_valid(color_str)

            except ValueError as e:
                self.logger.debug(
                    f"{ws.remote_address} choose invalid color: {e}"
                )
                await self.send_dict_to_ws(
                    ws,
                    {
                        "type": "connection_error",
                        "data": f"Invalid snake color '{color_str}'\n{e}",
                    },
                )
                return

            await self.add_player(player_id, name, color)
            await self.send_dict_to_ws(
                ws, {"type": "set_server_desc", "data": self.config.server_desc}
            )

            await self.send_dict_to_ws(
                ws, {"type": "set_map_borders", "data": self.get_map_borders()}
            )
            is_ok = True
            return player_id
        except Exception as e:
            self.logger.exception(e)
        finally:
            self.logger.debug(f"Registration {self.get_pretty_address(ws)} finished: {is_ok}")

    async def handle_connection(self, ws):

        try:
            ws.max_size = 1024 * 1024  # 1MB

            player_id = await self.handle_registration(ws)
            if not player_id:
                return

            try:

                async for message in ws:
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
                await ws.close()
                return

        except Exception as e:
            self.logger.error(f"Unexpected error while handling connection {ws}: {e}")
            self.logger.exception(e)

        finally:
            if player_id:
                await self.remove_player(player_id)

            await ws.close()
            self.logger.debug("WS closed")

