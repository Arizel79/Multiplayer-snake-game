from server.mixins.base_mixin import BaseMixin
from server.modules.dto import *


class ViewportMixin(BaseMixin):
    def update_spatial_grid(self):
        new_grid = {}

        for xy, food in self.food.items():

            if xy not in new_grid:
                new_grid[xy] = {'food': [], 'snake_ids': set()}

            new_grid[xy]['food'].append(food)

        for player_id, snake in self.snakes.items():
            segments_to_check = [snake.body[0]]
            if len(snake.body) > 1:
                segments_to_check.append(snake.body[-1])

            for segment in segments_to_check:
                cell_x = segment.x // self.grid_cell_size
                cell_y = segment.y // self.grid_cell_size
                cell_key = (cell_x, cell_y)

                if cell_key not in new_grid:
                    new_grid[cell_key] = {'food': [], 'snake_ids': set()}

                new_grid[cell_key]['snake_ids'].add(player_id)

        self.spatial_grid = new_grid

    def get_viewport_for_snake(self, snake: Snake) -> Viewport:
        """Возвращает область видимости для змеи"""
        if not snake.body:
            return Viewport(0, 0, self.viewport_width, self.viewport_height)

        head = snake.body[0]
        viewport_width = int(self.viewport_width * self.viewport_scale_factor)
        viewport_height = int(self.viewport_height * self.viewport_scale_factor)

        return Viewport(head.x, head.y, viewport_width, viewport_height)

    def get_objects_in_viewport(self, viewport: Viewport):
        visible_snake_ids = set()
        visible_food = []

        start_x = max(viewport.left // self.grid_cell_size, -self.width // 2)
        end_x = min(viewport.right // self.grid_cell_size, self.width // 2)
        start_y = max(viewport.top // self.grid_cell_size, -self.height // 2)
        end_y = min(viewport.bottom // self.grid_cell_size, self.height // 2)

        left, right, top, bottom = viewport.left, viewport.right, viewport.top, viewport.bottom
        spatial_grid = self.spatial_grid

        for cell_x in range(int(start_x), int(end_x) + 1):
            for cell_y in range(int(start_y), int(end_y) + 1):
                cell_key = (cell_x, cell_y)
                if cell_key in spatial_grid:
                    cell_data = spatial_grid[cell_key]

                    for food in cell_data.get('food', []):
                        point = food.point
                        if left <= point.x <= right and top <= point.y <= bottom:
                            visible_food.append(food)

                    for player_id in cell_data.get('snake_ids', set()):
                        if player_id not in visible_snake_ids:
                            snake = self.snakes.get(player_id)
                            if snake and self._snake_intersects_viewport_fast(snake, viewport):
                                visible_snake_ids.add(player_id)

        return list(visible_snake_ids), visible_food

    def _snake_intersects_viewport_fast(self, snake: Snake, viewport: Viewport) -> bool:
        """Быстрая проверка пересечения змеи с viewport"""
        head = snake.body[0]
        if viewport.contains_point(head):
            return True

        tail = snake.body[-1]
        if viewport.contains_point(tail):
            return True

        if len(snake.body) > 2:
            middle_idx = len(snake.body) // 2
            middle = snake.body[middle_idx]
            if viewport.contains_point(middle):
                return True

        return False
