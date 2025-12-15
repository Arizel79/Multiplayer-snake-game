import argparse
import asyncio
import copy
import json
import logging
import random
import sys
from collections import deque
from dataclasses import dataclass
from time import time
import websockets

from config import MIN_LENGHT_FAST_ON


@dataclass
class Point:
    x: int
    y: int


@dataclass
class Food:
    point: Point
    type_: int
    color: str
    size: int


@dataclass
class Snake:
    body: deque
    direction: str
    next_direction: str
    color: str
    name: str
    size: int = 0
    max_size: int = size
    alive: bool = True
    is_fast: bool = False
    immortal: bool = False

    def remove_segment(self, n=1, min_pop_size=2):
        for i in range(n):
            if len(self.body) > min_pop_size:
                self.body.pop()
                self.size = len(self.body)
        if len(self.body) < MIN_LENGHT_FAST_ON:
            self.is_fast = False

    def add_segment(self, n=1):
        if n < 0:
            raise ValueError("Argument 'n' must be natural integer. ")
        for i in range(n):
            self.body.append(copy.copy(self.body[-1]))
        self.size = len(self.body)
        if len(self.body) > self.max_size:
            self.max_size = len(self.body)


@dataclass
class Player:
    player_id: str
    name: str
    color: str
    alive: bool
    deaths: int = 0
    kills: int = 0
    best_score: int = 0
    last_score: int = 0


@dataclass
class Viewport:
    center_x: int
    center_y: int
    width: int
    height: int

    @property
    def left(self):
        return self.center_x - self.width // 2

    @property
    def right(self):
        return self.center_x + self.width // 2

    @property
    def top(self):
        return self.center_y - self.height // 2

    @property
    def bottom(self):
        return self.center_y + self.height // 2

    def contains_point(self, point: Point) -> bool:
        return (self.left <= point.x <= self.right and
                self.top <= point.y <= self.bottom)

    def intersects_snake(self, snake: Snake) -> bool:
        for segment in snake.body:
            if self.contains_point(segment):
                return True
        return False
