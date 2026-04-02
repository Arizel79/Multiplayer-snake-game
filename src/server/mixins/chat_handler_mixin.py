import html

from src.server.mixins.base_mixin import *


class ChatHandlerMixin(BaseMixin):
    BOOL_TRUE_STR = ("t", "true", "y", "yes", "1")
    BOOL_FALSE_STR = ("f", "false", "n", "no", "0")

    class PlayerNotFound(Exception):
        pass

    class PlayerNotSpecified(Exception):
        pass

    def parse_str_bool(self, bool_str, default=None):
        bool_str = bool_str.lower()
        out = None
        if bool_str in self.BOOL_TRUE_STR:
            out = True
        elif bool_str in self.BOOL_FALSE_STR:
            out = False

        if out is None:
            out = default
        return out

    async def _handle_command_admin(self, player_id, args):
        self.logger.info(f"player {self.get_player(player_id)} want to be admin")
        try:
            password = args[0]
        except IndexError:
            password = None
        if self.config.admin_password and password == self.config.admin_password:
            await self.set_player_is_admin(player_id)

            await self.send_dict_to_player(
                player_id,
                {"type": "chat_message", "data": "You are admin now"},
            )
        else:
            self.logger.info(
                f"Player {self.get_player(player_id)} send wrong admin password: {password}"
            )
            await self.send_message_or_error(
                player_id, "Wrong admin password", is_error=True
            )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.ADMIN_COMMANDS = {
            "kick": ("/kick",),
            "kill": ("/kill",),
            "set_size": ("/setsize", "/set_size", "/s"),
            "set_frozen": ("/frozen", "/set_frozen", "/freeze", "/fr", "/f"),
            "set": {"/set", "/param"},
        }
        self.ALL_ADMIN_COMMANDS = []
        for k, v in self.ADMIN_COMMANDS.items():
            self.ALL_ADMIN_COMMANDS += v

    async def send_message_or_error(self, player_id, text, is_error=False):
        if is_error:
            text = f"<red>{html.escape(text)}</red>"
        await self.send_dict_to_player(
            player_id, {"type": "chat_message", "data": text}
        )

    async def _handle_command_killme(self, player_id, args):

        self.logger.info(f"player {self.get_player(player_id)} want kill himself")
        await self.player_death(player_id, "%NAME% committed suicide", if_immortal=True)

    async def _handle_command_kill(self, player_id, args):
        try:
            self.logger.info(f"Killing {player_id}")
            try:
                target_player = self.get_player_by_name(args[0])
            except IndexError:
                raise self.PlayerNotSpecified
            if not target_player:
                raise self.PlayerNotFound()
            await self.player_death(target_player.player_id, if_immortal=True)
            await self.send_message_or_error(
                player_id, f"Player {target_player.name} killed"
            )
        except self.PlayerNotFound:
            await self.send_message_or_error(
                player_id, f"Player not found", is_error=True
            )
        except self.PlayerNotSpecified:
            await self.send_message_or_error(
                player_id, f"Player not specified", is_error=True
            )

    async def _handle_command_kick_me(self, player_id, args):
        self.logger.info(
            f"player {self.get_player(player_id)} want kick himself from server"
        )
        await self.remove_player(player_id)

    async def _handle_command_kick(self, player_id, args):
        try:
            self.logger.info(f"Kicking {player_id} from server")
            target_player = self.get_player_by_name(args[0])
            if not target_player:
                raise self.PlayerNotFound()
            await self.remove_player(target_player.player_id)
            if player_id != target_player.player_id:
                await self.send_message_or_error(
                    player_id, f"Player {target_player.player_id} kicked"
                )
        except self.PlayerNotFound:
            await self.send_message_or_error(
                player_id, f"Player not found", is_error=True
            )
        except (IndexError, ValueError) as e:
            self.logger.debug(f"Error in _handle_command_kick: {e}")
            await self.send_message_or_error(player_id, f"Error", is_error=True)
        except Exception as e:
            self.logger.exception(e)

    async def _handle_command_set(self, player_id, args):
        try:
            self.logger.info(f"Command set: {args}")
            try:
                param = args[0]
                value = args[1]
            except IndexError as e:
                self.logger.exception(e)
                await self.send_message_or_error(
                    player_id, f"Error parsing", is_error=True
                )
                return
            if param == "chat_enable":
                enable_chat = self.parse_str_bool(value)
                if enable_chat is None:
                    raise ValueError

                self.config.enable_chat = enable_chat
                self.logger.info(f"Set {self.config.enable_chat=}")
            else:
                await self.send_message_or_error(
                    player_id, f"Unknown param: {param}", is_error=True
                )
                return
        except ValueError:
            await self.send_message_or_error(player_id, f"Error value", is_error=True)
        except Exception as e:
            self.logger.exception(e)
            await self.send_message_or_error(player_id, f"Error", is_error=True)

    async def _handle_command_set_size(self, player_id, args):
        try:
            self.logger.info(f"Setting size {player_id}")
            if len(args) == 2:
                try:
                    target_player = self.get_player_by_name(args[0])
                except IndexError:
                    raise self.PlayerNotSpecified

                new_size = int(args[1])
            elif len(args) == 1:
                target_player = self.players[player_id]
                new_size = int(args[0])
            else:
                raise ValueError
            if not target_player:
                raise self.PlayerNotFound()

            await self.set_snake_size(target_player.player_id, new_size=new_size)
            await self.send_message_or_error(
                player_id, f"Player {target_player.name} size updated: {new_size}"
            )

        except self.PlayerNotFound:
            await self.send_message_or_error(
                player_id, f"Player not found", is_error=True
            )
        except self.PlayerNotSpecified:
            await self.send_message_or_error(
                player_id, f"Player not specified", is_error=True
            )
        except ValueError:
            await self.send_message_or_error(
                player_id, f"Error setting size", is_error=True
            )
        except Exception as e:
            self.logger.exception(e)

    async def _handle_command_freeze_player(self, player_id, args):
        try:
            self.logger.debug(f"Freezing command by player {player_id}: {args}")

            if not args:
                raise self.PlayerNotSpecified

            target_player_id = None
            is_frozen = None

            first_arg = args[0].lower()

            self_unfreeze_symbols = self.BOOL_FALSE_STR
            self_freeze_symbols = self.BOOL_TRUE_STR

            if first_arg in self_unfreeze_symbols:
                target_player_id = player_id
                is_frozen = False

            elif first_arg in self_freeze_symbols:
                target_player_id = player_id
                is_frozen = True

            else:
                try:
                    target_player = self.get_player_by_name(args[0])
                    target_player_id = target_player.player_id
                except IndexError:
                    raise self.PlayerNotSpecified

                if len(args) > 1:
                    is_frozen_str = args[1].lower()
                    is_frozen = self.parse_str_bool(is_frozen_str, default=True)
                else:
                    is_frozen = True

            target_player = self.players[target_player_id]

            await self.set_is_player_frozen(target_player_id, is_frozen=is_frozen)

            await self.send_message_or_error(
                player_id, f"Player {target_player.name} set is frozen: {is_frozen}"
            )

        except self.PlayerNotFound:
            await self.send_message_or_error(
                player_id, f"Player not found", is_error=True
            )
        except self.PlayerNotSpecified:
            await self.send_message_or_error(
                player_id, f"Player not specified", is_error=True
            )
        except ValueError:
            await self.send_message_or_error(
                player_id, f"Error setting size", is_error=True
            )
        except Exception as e:
            self.logger.exception(e)

    async def handle_client_chat_message(self, player_id, message: str):
        con = self.connections[player_id]

        if message.startswith("/"):
            self.logger.info(
                f"{self.get_player(player_id)} issued server command: {message}"
            )
            command_and_args = message.split()
            args = command_and_args[1:]
            is_player_admin = self.players[player_id].is_admin

            if command_and_args[0] == "/help":
                await self.send_message_or_error(f"Help message here?")

            elif command_and_args[0] == "/killme":
                await self._handle_command_killme(player_id, args)

            elif command_and_args[0] == "/kickme":
                await self._handle_command_kick_me(player_id, args)

            elif command_and_args[0] == "/admin":
                await self._handle_command_admin(player_id, args)

            elif command_and_args[0] in self.ALL_ADMIN_COMMANDS:
                if is_player_admin:
                    self.logger.info(
                        f"Admin access allowed to {self.get_player(player_id)}"
                    )
                else:
                    self.logger.info(
                        "Admin access allowed to {self.get_player(player_id)}"
                    )
                    await self.send_message_or_error(
                        player_id, "Access denied. You are not admin", is_error=True
                    )
                    return

                if command_and_args[0] in self.ADMIN_COMMANDS["kick"]:
                    await self._handle_command_kick(player_id, args)

                if command_and_args[0] in self.ADMIN_COMMANDS["kill"]:
                    await self._handle_command_kill(player_id, args)

                if command_and_args[0] in self.ADMIN_COMMANDS["set"]:
                    await self._handle_command_set(player_id, args)

                if command_and_args[0] in self.ADMIN_COMMANDS["set_size"]:
                    await self._handle_command_set_size(player_id, args)
                elif command_and_args[0] in self.ADMIN_COMMANDS["set_frozen"]:
                    await self._handle_command_freeze_player(player_id, args)

        else:
            name = self.players[player_id].name
            if not self.config.enable_chat and (not self.players[player_id].is_admin):
                self.logger.debug(
                    f"{self.get_player(player_id)} tries write to chat but it disabled (message: {message})"
                )
                await self.send_dict_to_player(
                    player_id,
                    {
                        "type": "chat_message",
                        "data": f"<red>Chat disabled</red>",
                    },
                )
                return

            if len(message) > self.config.max_chat_message_length:
                size_comment = (
                    f"{len(message)}, max: {self.config.max_chat_message_length}"
                )
                self.logger.debug(
                    f"{self.get_player(player_id)} tries write to chat but message too long ({size_comment}) (message: {message})"
                )
                await self.send_dict_to_player(
                    player_id,
                    {
                        "type": "chat_message",
                        "data": f"<red>Message to long ({size_comment})</red>",
                    },
                )
                return
            self.logger.info(f"{self.get_player(player_id)} writes in chat: {message}")

            await self.broadcast_chat_message(
                {
                    "type": "chat_message",
                    "data": f"{message}",
                    "from_user": f"{await self.get_stilizate_name_color(player_id)}",
                }
            )
