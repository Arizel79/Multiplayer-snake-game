import json

from server.mixins.base_mixin import *


class ChatHandlerMixin(BaseMixin):
    async def handle_client_chat_message(self, player_id, message: str):
        ADMIN_COMMANDS = {
            "kick": ("/kick",),
            "kill": ("/kill",)
        }
        ALL_ADMIN_COMMANDS = []
        for k, v in ADMIN_COMMANDS.items():
            ALL_ADMIN_COMMANDS += v

        con = self.connections[player_id]

        if message.startswith("/"):
            self.logger.info(f"{self.get_player(player_id)} issued server command: {message}")
            lst = message.split()
            is_player_admin = self.players[player_id].is_admin
            if lst[0] == "/help":
                await con.send(json.dumps({"type": "chat_message",
                                           "data": f"Help mesaage here?"}))
            elif lst[0] == "/kill":
                self.logger.info(f"player {self.get_player(player_id)} want kill himself")
                await self.player_death(player_id, "%NAME% committed suicide", if_immortal=True)
            elif lst[0] == "/kickme":
                self.logger.info(f"player {self.get_player(player_id)} want kick himself from server")
                await self.remove_player(player_id)

            elif lst[0] == "/admin":
                self.logger.info(f"player {self.get_player(player_id)} want to be admin")
                try:
                    password = lst[1]
                except IndexError:
                    password = None
                if self.admin_password and password == self.admin_password:
                    self.players[player_id].is_admin = True
                    self.logger.info(f"Player {self.get_player(player_id)} are admin")
                    await self.send_dict_to_player(player_id, {"type": "chat_message", "data": "You are admin!"})
                else:
                    self.logger.info(f"Player {self.get_player(player_id)} send wrong admin password: {password}")
                    await self.send_dict_to_player(player_id, {"type": "chat_message", "data": "Wrong admin password!"})

            elif lst[0] in ALL_ADMIN_COMMANDS:
                if is_player_admin:
                    self.logger.info("access allowed")
                else:
                    self.logger.info("access denied")
                if lst[0] in ADMIN_COMMANDS["kick"]:
                    pass

        else:
            self.logger.info(f"{self.get_player(player_id)} writes in chat: {message}")
            name = self.players[player_id].name
            await self.broadcast_chat_message(
                {"type": "chat_message", "data": f"{message}",
                 "from_user": f"{await self.get_stilizate_name_color(player_id)}"})
