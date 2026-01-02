import html

from server.mixins.base_mixin import *


class ChatHandlerMixin(BaseMixin):
    class PlayerNotFound(Exception):
        pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.ADMIN_COMMANDS = {"kick": ("/kick",), "kill": ("/kill",)}
        self.ALL_ADMIN_COMMANDS = []
        for k, v in self.ADMIN_COMMANDS.items():
            self.ALL_ADMIN_COMMANDS += v

    async def handle_client_chat_message(self, player_id, message: str):
        con = self.connections[player_id]

        async def send_message(text, is_error=False):
            if is_error:
                text = f"<red>{html.escape(text)}</red>"
            await self.send_dict_to_player(
                player_id, {"type": "chat_message", "data": text}
            )

        if message.startswith("/"):
            self.logger.info(
                f"{self.get_player(player_id)} issued server command: {message}"
            )
            lst = message.split()
            is_player_admin = self.players[player_id].is_admin
            if lst[0] == "/help":
                await send_message(f"Help message here?")

            elif lst[0] == "/killme":
                self.logger.info(
                    f"player {self.get_player(player_id)} want kill himself"
                )
                await self.player_death(
                    player_id, "%NAME% committed suicide", if_immortal=True
                )
            elif lst[0] == "/kickme":
                self.logger.info(
                    f"player {self.get_player(player_id)} want kick himself from server"
                )
                await self.remove_player(player_id)

            elif lst[0] == "/admin":
                self.logger.info(
                    f"player {self.get_player(player_id)} want to be admin"
                )
                try:
                    password = lst[1]
                except IndexError:
                    password = None
                if (
                        self.config.admin_password
                        and password == self.config.admin_password
                ):
                    self.players[player_id].is_admin = True
                    self.logger.info(
                        f"Player {self.get_player(player_id)} set to admin"
                    )
                    await self.send_dict_to_player(
                        player_id,
                        {"type": "chat_message", "data": "You are admin now!"},
                    )
                else:
                    self.logger.info(
                        f"Player {self.get_player(player_id)} send wrong admin password: {password}"
                    )
                    await send_message("Wrong admin password!", is_error=True)

            elif lst[0] in self.ALL_ADMIN_COMMANDS:
                if is_player_admin:
                    self.logger.info("access allowed")
                else:
                    self.logger.info("access denied")
                    await send_message("Access denied!", is_error=True)
                    return

                if lst[0] in self.ADMIN_COMMANDS["kick"]:
                    try:
                        self.logger.info(f"Kicking {player_id} from server")
                        target_player = self.get_player_by_name(lst[1])
                        if not target_player:
                            raise self.PlayerNotFound()
                        await self.remove_player(target_player.player_id)
                        if player_id != target_player.player_id:
                            await send_message(f"Player {player_id} kicked")
                    except self.PlayerNotFound:
                        await send_message(f"Player not found!", is_error=True)
                    except Exception as e:
                        self.logger.exception(e)

                if lst[0] in self.ADMIN_COMMANDS["kill"]:
                    try:
                        self.logger.info(f"Killing {player_id}")
                        target_player = self.get_player_by_name(lst[1])
                        if not target_player:
                            raise self.PlayerNotFound()
                        await self.player_death(
                            target_player.player_id, if_immortal=True
                        )
                        await send_message(f"Player {player_id} killed")
                    except self.PlayerNotFound:
                        await send_message(f"Player not found!", is_error=True)
                    except Exception as e:
                        self.logger.exception(e)

        else:
            name = self.players[player_id].name
            if not self.config.enable_chat and (not self.players[player_id].is_admin):
                self.logger.debug(f"{self.get_player(player_id)} tries write to chat but it disabled (message: {message})")
                await self.send_dict_to_player(player_id, {
                    "type": "chat_message",
                    "data": f"<red>Chat disabled</red>",
                })
                return

            if len(message) > self.config.max_chat_message_length:
                size_comment = f"{len(message)}, max: {self.config.max_chat_message_length}"
                self.logger.debug(
                    f"{self.get_player(player_id)} tries write to chat but message too long ({size_comment}) (message: {message})")
                await self.send_dict_to_player(player_id, {
                    "type": "chat_message",
                    "data": f"<red>Message to long ({size_comment})</red>",
                })
                return
            self.logger.info(f"{self.get_player(player_id)} writes in chat: {message}")

            await self.broadcast_chat_message(
                {
                    "type": "chat_message",
                    "data": f"{message}",
                    "from_user": f"{await self.get_stilizate_name_color(player_id)}",
                }
            )
