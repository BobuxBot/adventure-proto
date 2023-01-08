import os
import random
import sys
from typing import Literal

import exenworldgen
import keyboard
from exencolor import Color, Decoration, colored

"""
Objects reference
0 - free space
1 - wall
2 - player
3 - treasure
4 - trap
5 - heal
"""

COLORS = {
    -1: Color.GREY,
    0: Color.BLACK,
    1: Color.BRIGHT_WHITE,
    2: Color.BRIGHT_CYAN,
    3: Color.YELLOW,
    4: Color.BRIGHT_RED,
    5: Color.BRIGHT_GREEN,
}

Vector2 = tuple[int, int]
Direction = Literal[0, 1, 2, 3]


class World(exenworldgen.World):
    def __init__(self):
        super().__init__((15, 15))
        self.generate()

        self.free_positions: list[Vector2] = []
        for i in range(self.size[1]):
            for j in range(self.size[0]):
                if not self[i, j]:
                    self.free_positions.append((i, j))

        self.player_pos = random.choice(self.free_positions)
        self[self.player_pos] = 2
        self.free_positions.remove(self.player_pos)
        self.treasure_pos = random.choice(self.free_positions)
        self.free_positions.remove(self.treasure_pos)
        self[self.treasure_pos] = 3
        for pos in self.free_positions:
            self[pos] = random.choices([0, 4, 5], [1, 0.1, 0.1], k=1)[0]
        self.player_view = self.data.copy()
        for i in range(1, len(self.player_view) - 1):
            self.player_view[i] = [1] + [-1] * (self.size[0] - 2) + [1]
        self.subtext = colored(
            "Welcome! Use AWSD to move around.",
            foreground=Color.BRIGHT_YELLOW,
            decoration=Decoration.BOLD,
        )

    def print(self):
        txt = ""
        for row in self.player_view:
            for el in row:
                if el == 2:
                    txt += colored(f"P ", foreground=Color.BRIGHT_YELLOW)
                    continue
                elif el == -1:
                    txt += colored(f"? ", foreground=Color.GREY, background=Color.BLACK)
                    continue
                txt += colored(f"{el} ", foreground=COLORS[el], background=COLORS[el])
            txt += "\n"
        txt += "\n" + self.subtext
        os.system("cls")
        print(txt)

    def move_player(self, pos: Vector2):
        if self[pos] == 1:
            raise "There's a wall on position %s" % str(pos)
        self[self.player_pos] = 0
        self.player_view[self.player_pos[0]][self.player_pos[1]] = 0
        match v := self[pos]:  # noqa: E999
            case 0:
                self.subtext = colored("Nothing here...", foreground=Color.GREY)
            case 3:
                self.subtext = colored(
                    "TREASURE!", foreground=Color.YELLOW, decoration=Decoration.BOLD
                )
            case 4:
                self.subtext = colored(
                    "Trap!", foreground=Color.BRIGHT_RED, decoration=Decoration.BOLD
                )
            case 5:
                self.subtext = colored(
                    "Heal!", foreground=Color.BRIGHT_GREEN, decoration=Decoration.BOLD
                )
        self.subtext = f"{colored(pos, foreground=Color.BRIGHT_MAGENTA)} {self.subtext}"
        self[pos] = 2
        self.player_pos = pos
        return v

    def clear_fog(self, cell: Vector2):
        self.player_view[cell[0]][cell[1]] = self[cell]

    def clear_all_fog(self):
        self.player_view = self.data.copy()


class Player:
    def __init__(self, _world: World, money: int = 0):
        self.max_health = 100
        self.health = self.max_health
        self.money = money
        self.world = _world
        self.pos = self.world.player_pos
        self.clear_fog()

    def move(self, direction: Direction):
        next_pos = get_next_pos(self.pos, direction)
        if self.world[next_pos] != 1:
            v = self.world.move_player(next_pos)
            health_delta = ""
            money_delta = ""
            match v:
                case 3:
                    self.money += 1000
                    money_delta = "( + 1000 )"
                case 4:
                    self.health -= 10
                    if self.health <= 0:
                        print("You died lmao")
                        sys.exit(0)
                    health_delta = "( - 10 )"
                case 5:
                    self.health += 10
                    if self.health > self.max_health:
                        self.health = self.max_health
                    health_delta = "( + 10 )"
            health_str = colored(
                f"❤️ Health: "
                + colored(
                    f"{self.health}/{self.max_health} {health_delta}",
                    decoration=Decoration.BOLD,
                ),
                foreground=Color.BRIGHT_RED,
            )
            money_str = colored(
                f"🪙 Money: "
                + colored(f"{self.money:,} {money_delta}", decoration=Decoration.BOLD),
                foreground=Color.BRIGHT_YELLOW,
            )
            self.world.subtext += "\n" + health_str + "\n" + money_str
            self.pos = next_pos
        self.clear_fog()
        self.world.print()

    def clear_fog(self):
        self.world.clear_fog(self.pos)
        for cell in self.round_cells:
            if self.world[cell] == 1:
                self.world.clear_fog(cell)

    @property
    def round_cells(self) -> list[Vector2]:
        diagonals = [
            (self.pos[0] - 1, self.pos[1] - 1),
            (self.pos[0] - 1, self.pos[1] + 1),
            (self.pos[0] + 1, self.pos[1] - 1),
            (self.pos[0] + 1, self.pos[1] + 1),
        ]
        return [get_next_pos(self.pos, i) for i in range(4)] + diagonals  # type: ignore


def get_next_pos(pos: Vector2, direction: Direction):
    match direction:
        case 0:
            return pos[0] - 1, pos[1]
        case 1:
            return pos[0], pos[1] + 1
        case 2:
            return pos[0] + 1, pos[1]
        case 3:
            return pos[0], pos[1] - 1


world = World()
player = Player(world)
world.print()

while True:
    try:
        key: keyboard.KeyboardEvent = keyboard.read_event()
        if key.event_type != "down":
            continue
    except KeyboardInterrupt:
        break
    match key.name:
        case "w":
            player.move(0)
        case "d":
            player.move(1)
        case "s":
            player.move(2)
        case "a":
            player.move(3)
        case "r":
            world = World()
            player = Player(world, player.money)
            world.print()
        case "c":
            world.clear_all_fog()
            world.print()
        case "esc":
            break
