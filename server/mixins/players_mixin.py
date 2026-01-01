import json

from server.mixins.base_mixin import BaseMixin
from server.modules.config import *
from server.modules.dataclasses import *


class PlayersMixin(BaseMixin):
    async def add_player(self, player_id: str, name, color):
        if player_id in self.snakes:
            return False
        self.players[player_id] = Player(
            player_id=player_id, name=name, color=color, alive=True
        )

        await self.spawn(player_id)
        await self.broadcast_chat_message(
            {
                "type": "chat_message",
                "subtype": "join/left",
                "data": f"<yellow>[</yellow><green>+</green><yellow>]</yellow> {await self.get_stilizate_name_color(player_id)} <yellow>joined the game</yellow>",
            }
        )
        self.logger.info(
            f"Connection {self.get_addres_from_ws(self.connections[player_id])} registred as {self.get_player(player_id)}"
        )
        return True

    async def remove_player(self, player_id):
        if player_id not in self.players.keys():
            return True
        self.logger.info(f"Player {self.get_player(player_id)} disconnected")
        await self.connections[player_id].close()
        del self.connections[player_id]
        await self.broadcast_chat_message(
            {
                "type": "chat_message",
                "subtype": "join/left",
                "data": f"<yellow>[</yellow><red>-</red><yellow>]</yellow> {await self.get_stilizate_name_color(player_id)} <yellow>left the game</yellow>",
            }
        )

        if player_id in self.snakes:
            del self.snakes[player_id]
        if player_id in self.players:
            del self.players[player_id]

        self._send_cache_for_players.clear()

        return True

    def change_direction(self, player_id, direction):
        if player_id in self.snakes:
            snake = self.snakes[player_id]

            if (
                (
                    direction == "up"
                    and snake.direction != "down"
                    and snake.next_direction != "down"
                )
                or (
                    direction == "down"
                    and snake.direction != "up"
                    and snake.next_direction != "up"
                )
                or (
                    direction == "left"
                    and snake.direction != "right"
                    and snake.next_direction != "right"
                )
                or (
                    direction == "right"
                    and snake.direction != "left"
                    and snake.next_direction != "left"
                )
            ):
                snake.next_direction = direction

    async def player_death(
        self, player_id, reason: str = "Player %NAME% death", if_immortal=False
    ):
        if self.snakes[player_id].immortal and not if_immortal:
            return False
        if not self.snakes[player_id].alive:
            raise ValueError(f"Snake {player_id} is already death!")

        sn = self.snakes[player_id]
        pl = self.players[player_id]
        self.snakes[player_id].alive = False
        body = self.snakes[player_id].body

        self.players[player_id].alive = False
        self.players[player_id].deaths += 1

        text = f'{reason.replace("%NAME%", await self.get_stilizate_name_color(player_id))}'
        self.logger.info(f"Player {self.get_player(player_id)} death ({text})")

        await self.connections[player_id].send(
            json.dumps(
                {
                    "type": "you_died",
                    "data": text,
                    "stats": {
                        "size": sn.size,
                        "max_size": sn.max_size,
                        "deaths": pl.deaths,
                        "kills": pl.kills,
                    },
                }
            )
        )
        await self.broadcast_chat_message(
            {
                "type": "chat_message",
                "subtype": "death_message",
                "data": text,
                "player_id": player_id,
            }
        )
        for n, i in enumerate(body):
            self.add_food(
                i.x,
                i.y,
                type_=FOOD_TYPES.death,
                color=self.get_color_for_segment(sn, n),
            )

        return True

    def get_player(self, player_id):

        try:
            address = "@" + self.get_addres_from_ws(self.connections[player_id])
        except KeyError:
            address = ""
        return f"{self.players[player_id].name}{address}"

    def get_player_by_name(self, player_name):

        for k, v in self.players.items():
            if v.name == player_name:
                return v

