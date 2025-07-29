# client_gui.py
import asyncio
import json
import sys
import re
import random

import pygame
from pygame.locals import *

from client_base import ClientBase

def remove_html_tags(text):
    clean_text = re.sub(r'<[^>]*>', '', text)
    return clean_text

class ClientGUI(ClientBase):
    def __init__(self, *args, interactive=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.version = f"{self.version} (GUI)"

        # Pygame initialization
        pygame.init()
        pygame.display.set_caption("Multiplayer Snake Game")

        # Window settings
        self.default_width = 800
        self.default_height = 600
        self.screen = pygame.display.set_mode((self.default_width, self.default_height), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.FPS = 60

        # Colors
        self.BG_COLOR = (20, 20, 20)
        self.GRID_COLOR = (40, 40, 40)
        self.TEXT_COLOR = (255, 255, 255)

        # Fonts
        self.font_small = pygame.font.SysFont('Arial', 14)
        self.font_medium = pygame.font.SysFont('Arial', 18)
        self.font_large = pygame.font.SysFont('Arial', 24)

        # UI elements
        self.chat_active = False
        self.chat_input = ""
        self.chat_messages = []
        self.MAX_CHAT_MESSAGES = 10
        self.show_debug = False
        self.show_tablist = False

    def add_chat_message(self, message):
        """Add a message to chat history"""
        self.chat_messages.append(message)
        if len(self.chat_messages) > self.MAX_CHAT_MESSAGES:
            self.chat_messages.pop(0)

    def render_chat_messages(self):
        """Render chat messages on screen"""
        width, height = self.screen.get_size()
        chat_y = height - 100 if self.chat_active else height - 40
        max_messages = 5 if self.chat_active else 3

        # Chat background
        if len(self.chat_messages) > 0:
            pygame.draw.rect(self.screen, (0, 0, 0, 150),
                             (5, chat_y - (max_messages * 20) - 5,
                              width - 10, (max_messages * 20) + 5))

        # Render messages
        for i, message in enumerate(self.chat_messages[-max_messages:]):
            # Simple HTML-like tag parsing for colors
            color = self.TEXT_COLOR
            text = message
            if "<red>" in message:
                color = (255, 50, 50)
                text = text.replace("<red>", "").replace("</red>", "")
            elif "<green>" in message:
                color = (50, 255, 50)
                text = text.replace("<green>", "").replace("</green>", "")
            elif "<cyan>" in message:
                color = (50, 255, 255)
                text = text.replace("<cyan>", "").replace("</cyan>", "")
            elif "<yellow>" in message:
                color = (255, 255, 50)
                text = text.replace("<yellow>", "").replace("</yellow>", "")

            msg_text = self.font_small.render(text, True, color)
            self.screen.blit(msg_text, (10, chat_y - (max_messages - i) * 20))

    def render_chat_input(self):
        """Render chat input box"""
        width, height = self.screen.get_size()

        # Chat input box
        input_box = pygame.Rect(10, height - 40, width - 20, 30)
        pygame.draw.rect(self.screen, (50, 50, 50), input_box)
        pygame.draw.rect(self.screen, (100, 100, 100), input_box, 2)

        # Chat input text
        input_text = self.font_medium.render(f"> {self.chat_input}", True, self.TEXT_COLOR)
        self.screen.blit(input_text, (input_box.x + 5, input_box.y + 5))

        # Render chat messages above input
        self.render_chat_messages()

    def handle_chat_message(self, message):
        """Process incoming chat messages"""
        from_user = message.get("from_user", None)
        subtype = message.get("subtype", "chat_message")

        if subtype == "death_message":
            self.add_chat_message(f"[DEATH] {message.get('data', '')}")
        elif subtype == "join/left":
            self.add_chat_message(message.get('data', ''))
        elif subtype == "chat_message":
            if from_user is not None:
                self.add_chat_message(f"{from_user}: {message.get('data', '')}")
            else:
                self.add_chat_message(message.get('data', ''))

    def render(self):
        self.screen.fill(self.BG_COLOR)

        if self.state == "game" and self.game_state:
            self.render_game()
        elif self.state == "died":
            self.render_death_screen()
        elif self.state == "alert":
            self.render_alert()

        # Always render chat messages if they exist
        if len(self.chat_messages) > 0:
            self.render_chat_messages()

        if self.chat_active:
            self.render_chat_input()

        if self.show_tablist:
            self.render_tablist()

        if self.show_debug:
            self.render_debug_info()

        pygame.display.flip()
        self.clock.tick(self.FPS)

    def input_output_thread_worker(self):
        """Pygame handles input in main thread, so this is empty"""
        pass

    async def handle_input(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
                pygame.quit()
                sys.exit()

            elif event.type == VIDEORESIZE:
                # Handle window resize
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

            elif event.type == KEYDOWN:
                if self.state == "game":
                    if self.chat_active:
                        if event.key == K_RETURN:
                            await self.send_chat()
                            self.chat_active = False
                        elif event.key == K_BACKSPACE:
                            self.chat_input = self.chat_input[:-1]
                        elif event.key == K_ESCAPE:
                            self.chat_active = False
                        else:
                            self.chat_input += event.unicode
                    else:
                        if event.key == K_t:
                            self.chat_active = True
                        elif event.key == K_TAB:
                            self.show_tablist = not self.show_tablist
                        elif event.key == K_F3:
                            self.show_debug = not self.show_debug
                        elif event.key in [K_w, K_UP]:
                            await self.websocket.send(json.dumps({"type": "direction", "data": "up"}))
                        elif event.key in [K_s, K_DOWN]:
                            await self.websocket.send(json.dumps({"type": "direction", "data": "down"}))
                        elif event.key in [K_a, K_LEFT]:
                            await self.websocket.send(json.dumps({"type": "direction", "data": "left"}))
                        elif event.key in [K_d, K_RIGHT]:
                            await self.websocket.send(json.dumps({"type": "direction", "data": "right"}))
                        elif event.key == K_q:
                            self.running = False
                elif self.state == "died" and event.key == K_SPACE:
                    await self.websocket.send(json.dumps({"type": "respawn"}))
                elif self.state == "alert" and event.key == K_SPACE:
                    self.state = None
        self.render()

    def render_game(self):
        # Draw game grid
        width, height = self.screen.get_size()
        # cell_size = min(width // (self.game_state["map_borders"][2] - self.game_state["map_borders"][0] + 2),
        #                 height // (self.game_state["map_borders"][3] - self.game_state["map_borders"][1] + 2))
        cell_size = 20

        # Calculate visible area
        if self.player_id in self.game_state["snakes"]:
            head = self.game_state["snakes"][self.player_id]["body"][0]
            center_x, center_y = head["x"], head["y"]
        else:
            center_x, center_y = 0, 0

        # Draw grid
        for x in range(self.game_state["map_borders"][0], self.game_state["map_borders"][2] + 1):
            for y in range(self.game_state["map_borders"][1], self.game_state["map_borders"][3] + 1):
                screen_x = width // 2 + (x - center_x) * cell_size
                screen_y = height // 2 + (y - center_y) * cell_size

                if (screen_x >= 0 and screen_x <= width and
                        screen_y >= 0 and screen_y <= height):
                    pygame.draw.rect(self.screen, self.GRID_COLOR,
                                     (screen_x, screen_y, cell_size, cell_size), 1)

        # Draw border
        border_color = (100, 100, 100)
        min_x, min_y, max_x, max_y = self.game_state["map_borders"]
        for x in [min_x - 1, max_x + 1]:
            for y in range(min_y - 1, max_y + 2):
                screen_x = width // 2 + (x - center_x) * cell_size
                screen_y = height // 2 + (y - center_y) * cell_size
                pygame.draw.rect(self.screen, border_color,
                                 (screen_x, screen_y, cell_size, cell_size))

        for y in [min_y - 1, max_y + 1]:
            for x in range(min_x - 1, max_x + 2):
                screen_x = width // 2 + (x - center_x) * cell_size
                screen_y = height // 2 + (y - center_y) * cell_size
                pygame.draw.rect(self.screen, border_color,
                                 (screen_x, screen_y, cell_size, cell_size))

        # Draw food
        for food in self.game_state["food"]:
            screen_x = width // 2 + (food["x"] - center_x) * cell_size
            screen_y = height // 2 + (food["y"] - center_y) * cell_size
            pygame.draw.circle(self.screen, (255, 50, 50),
                               (screen_x + cell_size // 2, screen_y + cell_size // 2),
                               cell_size // 3)

        # Draw snakes
        for snake_id, snake in self.game_state["snakes"].items():
            if not snake["alive"]:
                color = (100, 100, 100)  # Gray for dead snakes
            else:
                color_map = {
                    "red": (255, 50, 50),
                    "green": (50, 255, 50),
                    "blue": (50, 50, 255),
                    "yellow": (255, 255, 50),
                    "magenta": (255, 50, 255),
                    "cyan": (50, 255, 255)
                }
                color = color_map.get(snake["color"], (200, 200, 200))

            for i, segment in enumerate(snake["body"]):
                screen_x = width // 2 + (segment["x"] - center_x) * cell_size
                screen_y = height // 2 + (segment["y"] - center_y) * cell_size

                if i == 0:  # Head
                    pygame.draw.rect(self.screen, color,
                                     (screen_x, screen_y, cell_size, cell_size))
                    # Draw eyes
                    eye_offset = cell_size // 4
                    if snake["direction"] == "up":
                        pygame.draw.circle(self.screen, (0, 0, 0),
                                           (screen_x + cell_size // 3, screen_y + eye_offset),
                                           cell_size // 8)
                        pygame.draw.circle(self.screen, (0, 0, 0),
                                           (screen_x + 2 * cell_size // 3, screen_y + eye_offset),
                                           cell_size // 8)
                    elif snake["direction"] == "down":
                        pygame.draw.circle(self.screen, (0, 0, 0),
                                           (screen_x + cell_size // 3, screen_y + cell_size - eye_offset),
                                           cell_size // 8)
                        pygame.draw.circle(self.screen, (0, 0, 0),
                                           (screen_x + 2 * cell_size // 3, screen_y + cell_size - eye_offset),
                                           cell_size // 8)
                    elif snake["direction"] == "left":
                        pygame.draw.circle(self.screen, (0, 0, 0),
                                           (screen_x + eye_offset, screen_y + cell_size // 3),
                                           cell_size // 8)
                        pygame.draw.circle(self.screen, (0, 0, 0),
                                           (screen_x + eye_offset, screen_y + 2 * cell_size // 3),
                                           cell_size // 8)
                    elif snake["direction"] == "right":
                        pygame.draw.circle(self.screen, (0, 0, 0),
                                           (screen_x + cell_size - eye_offset, screen_y + cell_size // 3),
                                           cell_size // 8)
                        pygame.draw.circle(self.screen, (0, 0, 0),
                                           (screen_x + cell_size - eye_offset, screen_y + 2 * cell_size // 3),
                                           cell_size // 8)
                else:  # Body
                    pygame.draw.rect(self.screen, color,
                                     (screen_x, screen_y, cell_size, cell_size))

        # Draw UI
        if self.player_id in self.game_state["snakes"]:
            snake = self.game_state["snakes"][self.player_id]
            score_text = self.font_medium.render(f"Size: {snake['size']}", True, self.TEXT_COLOR)
            self.screen.blit(score_text, (10, 10))

            controls_text = self.font_small.render("WASD: Move | T: Chat | TAB: Player list | F3: Debug", True,
                                                   self.TEXT_COLOR)
            self.screen.blit(controls_text, (10, height - 30))

    def render_death_screen(self):
        width, height = self.screen.get_size()

        # Dark overlay
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Death message
        title = self.font_large.render("YOU DIED", True, (255, 50, 50))
        title_rect = title.get_rect(center=(width // 2, height // 3))
        self.screen.blit(title, title_rect)

        # Reason
        reason = self.font_medium.render(self.alert_message, True, self.TEXT_COLOR)
        reason_rect = reason.get_rect(center=(width // 2, height // 2))
        self.screen.blit(reason, reason_rect)

        # Stats
        if self.player_id in self.game_state["players"]:
            player = self.game_state["players"][self.player_id]
            snake = self.game_state["snakes"].get(self.player_id, {})

            stats = [
                f"Size: {snake.get('size', 0)}",
                f"Max Size: {snake.get('max_size', 0)}",
                f"Kills: {player.get('kills', 0)}",
                f"Deaths: {player.get('deaths', 0)}"
            ]

            for i, stat in enumerate(stats):
                stat_text = self.font_medium.render(stat, True, self.TEXT_COLOR)
                stat_rect = stat_text.get_rect(center=(width // 2, height // 2 + 40 + i * 30))
                self.screen.blit(stat_text, stat_rect)

        # Instructions
        instructions = self.font_medium.render("Press SPACE to respawn", True, self.TEXT_COLOR)
        instructions_rect = instructions.get_rect(center=(width // 2, height - 100))
        self.screen.blit(instructions, instructions_rect)

    def render_alert(self):
        width, height = self.screen.get_size()

        # Dark overlay
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Alert box
        box_width = min(width - 40, 600)
        box_height = min(height - 40, 400)
        box_x = (width - box_width) // 2
        box_y = (height - box_height) // 2

        pygame.draw.rect(self.screen, (50, 50, 50), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, (100, 100, 100), (box_x, box_y, box_width, box_height), 2)

        # Title
        title = self.font_large.render("Alert", True, (255, 50, 50))
        title_rect = title.get_rect(center=(width // 2, box_y + 30))
        self.screen.blit(title, title_rect)

        # Message
        message_lines = self.alert_message.split('\n')
        for i, line in enumerate(message_lines):
            line_text = self.font_medium.render(line, True, self.TEXT_COLOR)
            line_rect = line_text.get_rect(center=(width // 2, box_y + 80 + i * 30))
            self.screen.blit(line_text, line_rect)

        # Instructions
        instructions = self.font_medium.render("Press SPACE to continue", True, self.TEXT_COLOR)
        instructions_rect = instructions.get_rect(center=(width // 2, box_y + box_height - 50))
        self.screen.blit(instructions, instructions_rect)

    async def wait_for_end(self):
        while self.state != None:
            await asyncio.sleep(.01)

    def render_tablist(self):
        width, height = self.screen.get_size()

        # Tablist background
        tablist_width = min(width - 40, 400)
        tablist_height = min(height - 40, 500)
        tablist_x = (width - tablist_width) // 2
        tablist_y = (height - tablist_height) // 2

        pygame.draw.rect(self.screen, (50, 50, 50), (tablist_x, tablist_y, tablist_width, tablist_height))
        pygame.draw.rect(self.screen, (100, 100, 100), (tablist_x, tablist_y, tablist_width, tablist_height), 2)

        # Title
        title = self.font_large.render("Player List", True, self.TEXT_COLOR)
        title_rect = title.get_rect(center=(width // 2, tablist_y + 30))
        self.screen.blit(title, title_rect)

        # Server info
        server_info = self.font_small.render(f"Server: {self.server_address}", True, self.TEXT_COLOR)
        self.screen.blit(server_info, (tablist_x + 10, tablist_y + 60))

        server_desc = self.font_small.render(self.server_desc, True, self.TEXT_COLOR)
        self.screen.blit(server_desc, (tablist_x + 10, tablist_y + 80))

        # Player count
        alive_count = sum(1 for p in self.game_state["players"].values() if p["alive"])
        dead_count = len(self.game_state["players"]) - alive_count
        count_text = self.font_medium.render(
            f"Players ({len(self.game_state['players'])}): Alive: {alive_count} | Dead: {dead_count}",
            True, self.TEXT_COLOR
        )
        self.screen.blit(count_text, (tablist_x + 10, tablist_y + 110))

        # Player list
        y_offset = tablist_y + 140
        for player_id, player in self.game_state["players"].items():
            snake = self.game_state["snakes"].get(player_id, {})

            # Player name and status
            color_map = {
                "red": (255, 50, 50),
                "green": (50, 255, 50),
                "blue": (50, 50, 255),
                "yellow": (255, 255, 50),
                "magenta": (255, 50, 255),
                "cyan": (50, 255, 255)
            }
            color = color_map.get(snake["color"], (200, 200, 200))

            # Player info
            status = "Alive" if player["alive"] else "Dead"
            status_color = (50, 255, 50) if player["alive"] else (255, 50, 50)

            name_text = self.font_medium.render(
                f"{player['name']} ({status})",
                True,
                color
            )
            self.screen.blit(name_text, (tablist_x + 10, y_offset))

            # Player stats
            stats_text = self.font_small.render(
                f"Size: {snake.get('size', 0)} | Max: {snake.get('max_size', 0)} | " +
                f"Kills: {player.get('kills', 0)} | Deaths: {player.get('deaths', 0)}",
                True,
                self.TEXT_COLOR
            )
            self.screen.blit(stats_text, (tablist_x + 30, y_offset + 25))

            # Highlight current player
            if player_id == self.player_id:
                pygame.draw.rect(
                    self.screen,
                    (100, 100, 255),
                    (tablist_x, y_offset - 5, tablist_width, 50),
                    2
                )

            y_offset += 50

    def render_debug_info(self):
        width, height = self.screen.get_size()

        # Debug info background
        debug_width = min(width - 40, 600)
        debug_height = min(height - 40, 400)
        debug_x = width - debug_width - 20
        debug_y = 20

        pygame.draw.rect(self.screen, (50, 50, 50), (debug_x, debug_y, debug_width, debug_height))
        pygame.draw.rect(self.screen, (100, 100, 100), (debug_x, debug_y, debug_width, debug_height), 2)

        # Title
        title = self.font_large.render("Debug Info", True, (50, 255, 255))
        self.screen.blit(title, (debug_x + 10, debug_y + 10))

        # State info
        state_text = self.font_medium.render(f"State: {self.state}", True, self.TEXT_COLOR)
        self.screen.blit(state_text, (debug_x + 10, debug_y + 40))

        # Player ID
        id_text = self.font_medium.render(f"Player ID: {self.player_id}", True, self.TEXT_COLOR)
        self.screen.blit(id_text, (debug_x + 10, debug_y + 70))

        # Game state info
        if self.game_state:
            snakes_count = len(self.game_state.get("snakes", {}))
            players_count = len(self.game_state.get("players", {}))
            food_count = len(self.game_state.get("food", []))

            stats_text = self.font_medium.render(
                f"Snakes: {snakes_count} | Players: {players_count} | Food: {food_count}",
                True,
                self.TEXT_COLOR
            )
            self.screen.blit(stats_text, (debug_x + 10, debug_y + 100))

    async def send_chat(self):
        if self.chat_input.strip():
            await self.websocket.send(json.dumps({
                "type": "chat_message",
                "data": self.chat_input
            }))
            self.chat_input = ""

    def quit(self):
        self.running = False
        pygame.quit()
        sys.exit()


if __name__ == '__main__':
    print("Don't run this file directly. Run client.py instead.")
