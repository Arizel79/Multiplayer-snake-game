import random

from server.mixins.base_mixin import BaseMixin
from server.modules.config import *
from server.modules.dataclasses import *


class SnakesMixin(BaseMixin):

    async def update_snake(self, player_id, snake):
        if not snake.alive:
            return

        should_move = (snake.is_fast and self.move_fast) or (
            not snake.is_fast and self.move_normal
        )
        if not should_move:
            return

        snake.direction = snake.next_direction
        head = snake.body[0]
        new_head = Point(head.x, head.y)

        direction_offsets = {
            "up": (0, -1),
            "down": (0, 1),
            "left": (-1, 0),
            "right": (1, 0),
        }
        dx, dy = direction_offsets[snake.direction]
        new_head.x += dx
        new_head.y += dy

        if await self.check_collision(player_id, new_head, head):
            return

        food_key = (new_head.x, new_head.y)
        if food_key in self.food:
            del self.food[food_key]
            snake.add_segment()

        snake.body.appendleft(new_head)
        snake.remove_segment()

    def check_collision_fast(self, player_id, point):
        """Быстрая проверка коллизий через spatial grid"""
        cell_x = point.x // self.config.grid_cell_size
        cell_y = point.y // self.config.grid_cell_size
        cell_key = (cell_x, cell_y)

        if cell_key in self.spatial_grid:
            for seg_x, seg_y, seg_player_id in self.spatial_grid[cell_key].get(
                "snake_segments", set()
            ):
                if point.x == seg_x and point.y == seg_y:
                    if seg_player_id != player_id:
                        return True
                    else:
                        snake = self.snakes[player_id]
                        if point != snake.body[0]:
                            return True
        return False

    async def check_collision(self, player_id, new_head, old_head):
        """Полная проверка коллизий со всеми змеями на карте"""

        walls = self.get_map_rect()
        if not (
            walls[0] <= new_head.x <= walls[2] and walls[1] <= new_head.y <= walls[3]
        ):
            await self.player_death(player_id, "%NAME% crashed into the border")
            return True

        for other_id, other_snake in self.snakes.items():
            if other_id == player_id:
                continue

            if other_snake.alive and self.point_in_snake_body(new_head, other_snake):
                await self.player_death(
                    player_id, f"%NAME% crashed into {other_snake.name}"
                )
                self.players[other_id].kills += 1
                return True

        snake = self.snakes.get(player_id)
        if snake is None:
            return
        if self.point_in_snake_body(new_head, snake, exclude_head=True):
            await self.player_death(player_id, "%NAME% crashed into his tail")
            return True

        return False

    def point_in_snake_body(self, point, snake, exclude_head=False):
        """Проверяет, находится ли точка в теле змеи"""
        start_index = 1 if exclude_head else 0
        for i in range(start_index, len(snake.body)):
            if point.x == snake.body[i].x and point.y == snake.body[i].y:
                return True
        return False

    async def is_move_now(self, now):

        move_normal = (
            now >= self.last_normal_snake_move_time + self.config.DEFAULT_MOVE_TIMEOUT
        )
        move_fast = (
            now >= self.last_fast_snake_move_time + self.config.FAST_MOVE_TIMEOUT
        )
        return move_normal, move_fast

    def _snake_to_dict(self, snake: Snake):
        return {
            "body": [{"x": p.x, "y": p.y} for p in snake.body],
            "color": snake.color,
            "name": snake.name,
            "size": snake.size,
            "max_size": snake.max_size,
            "alive": snake.alive,
            "direction": snake.direction,
            "is_fast": snake.is_fast,
        }

    async def toggle_speed(self, player_id, is_fast):
        if not self.config.fast_move_enable:
            self.logger.debug("Not toggle speed, fast move disable")
            return
        sn = self.snakes[player_id]
        if len(sn.body) < self.config.MIN_LENGHT_FAST_ON:
            return

        sn.is_fast = is_fast

    async def spawn(self, player_id, lenght=None):
        if not lenght:
            lenght = self.config.default_snake_length
        x, y = self.get_avalible_coords()
        self.players[player_id].alive = True
        body = deque([Point(x, y)])
        direction = random.choice(DIRECTIONS)
        sn = self.snakes[player_id] = Snake(
            body=body,
            direction=direction,
            next_direction=direction,
            color=self.players[player_id].color,
            name=self.players[player_id].name,
            alive=True,
        )

        sn.add_segment(lenght - 1)
        self.logger.info(
            f"Spawned {self.get_player(player_id)} ({self.players[player_id].name})"
        )

    async def respawn(self, player_id):
        await self.spawn(player_id)

    async def sometimes_steal_body(self, player_id):
        snake = self.snakes[player_id]
        if not snake.alive:
            return
        if random.random() < self.config.stealing_chance:
            current_length = len(snake.body)
            if current_length > self.config.min_stealing_snake_size:
                segments_to_remove = max(
                    1, int(current_length * self.config.steal_percentage)
                )
                self.logger.debug(
                    f"Stole {segments_to_remove} segments ({self.config.steal_percentage * 100}%) from {self.get_player(player_id)}"
                )

                snake.remove_segment(
                    segments_to_remove, min_pop_size=self.config.min_stealing_snake_size
                )

    async def fast_snake_steal_body(self, player_id):
        snake = self.snakes[player_id]

        if not snake.alive or not snake.is_fast:
            return

        if random.random() < self.config.fast_stealing_chance:
            current_length = len(snake.body)
            if current_length > self.config.min_stealing_snake_size:
                segments_to_remove = max(1, int(self.config.fast_steal_abs_size))

                for i in range(segments_to_remove):
                    segment_index = current_length - i - 1
                    if segment_index < 0:
                        break

                    point = snake.body[segment_index]
                    color = self.get_color_for_segment(snake, segment_index)

                    self.add_food(
                        point.x,
                        point.y,
                        type_=FOOD_TYPES.from_fast_snake,
                        color=color,
                        size=1,
                    )

                self.logger.debug(
                    f"FAST SPEED Stole {segments_to_remove} segments ({self.config.steal_percentage * 100}%) from {self.get_player(player_id)}"
                )

                snake.remove_segment(
                    segments_to_remove, min_pop_size=self.config.min_stealing_snake_size
                )
