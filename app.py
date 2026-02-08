from __future__ import annotations

import random
from typing import List, Tuple

from textual.app import App, ComposeResult
from textual.containers import Container, Grid, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Static, Button
from textual.events import Key

GRID_SIZE = 4


def pad_lines(text: str, height: int) -> str:
    lines = text.splitlines() if text else [""]
    if len(lines) >= height:
        return "\n".join(lines[:height])
    total_pad = height - len(lines)
    top = total_pad // 2
    bottom = total_pad - top
    return "\n".join([""] * top + lines + [""] * bottom)


class Tile(Static):
    VALUE_CLASSES = [
        "v0",
        "v2",
        "v4",
        "v8",
        "v16",
        "v32",
        "v64",
        "v128",
        "v256",
        "v512",
        "v1024",
        "v2048",
    ]

    def __init__(self) -> None:
        super().__init__(classes="fill-text")

    def set_value(self, value: int) -> None:
        for cls in self.VALUE_CLASSES:
            self.remove_class(cls)
        if value == 0:
            self.add_class("v0")
            self.update(pad_lines("", 5))
        else:
            self.add_class(f"v{value}")
            self.update(pad_lines(str(value), 5))


class Board(Grid):
    def __init__(self) -> None:
        super().__init__(id="board")
        self.tiles: List[Tile] = [Tile() for _ in range(GRID_SIZE * GRID_SIZE)]

    def compose(self) -> ComposeResult:
        for tile in self.tiles:
            yield tile

    def render_board(self, grid: List[List[int]]) -> None:
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                self.tiles[r * GRID_SIZE + c].set_value(grid[r][c])


class Game2048(App):
    CSS_PATH = "styles.tcss"

    def __init__(self) -> None:
        super().__init__()
        self.grid: List[List[int]] = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.score = 0
        self.board = Board()
        self.score_widget = Static(id="score", classes="fill-text")
        self.status_widget = Static(id="status", classes="fill-text")
        self.won = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Container(id="layout"):
            with Container(id="panel"):
                yield Static(
                    pad_lines("2048  VALENTINE EDITION  ❤ ❤ ❤", 5),
                    id="title",
                    classes="fill-text",
                )
                yield self.score_widget
                yield self.board
                yield self.status_widget
        yield Footer()

    def on_mount(self) -> None:
        self.reset_game()

    def on_key(self, event: Key) -> None:
        key = event.key
        if key in {"up", "w", "k"}:
            self.move("up")
        elif key in {"down", "s", "j"}:
            self.move("down")
        elif key in {"left", "a", "h"}:
            self.move("left")
        elif key in {"right", "d", "l"}:
            self.move("right")
        elif key in {"r"}:
            self.reset_game()
        elif key in {"q", "escape"}:
            self.exit()

    def reset_game(self) -> None:
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.score = 0
        self.won = False
        self.add_random_tile()
        self.add_random_tile()
        self.update_score()
        self.update_ui("NEW GAME! USE ARROWS/WASD. R TO RESTART, Q TO QUIT. ❤")

    def update_ui(self, status: str | None = None) -> None:
        self.board.render_board(self.grid)
        self.score_widget.update(pad_lines(f"HIGHEST TILE: {self.score}   ❤", 4))
        if status is not None:
            self.status_widget.update(pad_lines(status, 4))

    def add_random_tile(self) -> None:
        empties: List[Tuple[int, int]] = [
            (r, c)
            for r in range(GRID_SIZE)
            for c in range(GRID_SIZE)
            if self.grid[r][c] == 0
        ]
        if not empties:
            return
        r, c = random.choice(empties)
        self.grid[r][c] = 4 if random.random() < 0.1 else 2

    def move(self, direction: str) -> None:
        moved = False

        def merge_line(line: List[int]) -> Tuple[List[int], int, bool]:
            original = list(line)
            numbers = [n for n in line if n != 0]
            merged: List[int] = []
            score_gained = 0
            i = 0
            while i < len(numbers):
                if i + 1 < len(numbers) and numbers[i] == numbers[i + 1]:
                    value = numbers[i] * 2
                    merged.append(value)
                    score_gained += value
                    i += 2
                else:
                    merged.append(numbers[i])
                    i += 1
            merged.extend([0] * (GRID_SIZE - len(merged)))
            return merged, score_gained, merged != original

        def get_line(index: int) -> List[int]:
            if direction in {"left", "right"}:
                line = list(self.grid[index])
                return list(reversed(line)) if direction == "right" else line
            line = [self.grid[r][index] for r in range(GRID_SIZE)]
            return list(reversed(line)) if direction == "down" else line

        def set_line(index: int, line: List[int]) -> None:
            if direction in {"left", "right"}:
                if direction == "right":
                    line = list(reversed(line))
                self.grid[index] = line
            else:
                if direction == "down":
                    line = list(reversed(line))
                for r in range(GRID_SIZE):
                    self.grid[r][index] = line[r]

        for i in range(GRID_SIZE):
            line = get_line(i)
            merged, _score_gained, line_moved = merge_line(line)
            set_line(i, merged)
            if line_moved:
                moved = True

        if moved:
            self.add_random_tile()
            self.update_score()
            if self.is_game_over():
                self.update_ui("GAME OVER. PRESS R TO RESTART. ❤")
            else:
                self.update_ui()
            self.check_win()
        else:
            if self.is_game_over():
                self.update_ui("GAME OVER. PRESS R TO RESTART. ❤")

    def is_game_over(self) -> bool:
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                value = self.grid[r][c]
                if value == 0:
                    return False
                if r + 1 < GRID_SIZE and self.grid[r + 1][c] == value:
                    return False
                if c + 1 < GRID_SIZE and self.grid[r][c + 1] == value:
                    return False
        return True

    def update_score(self) -> None:
        self.score = max(max(row) for row in self.grid)

    def check_win(self) -> None:
        if self.won:
            return
        if self.score >= 512:
            self.won = True
            self.push_screen(ValentineScreen())


class ValentineScreen(ModalScreen):
    HEART_FRAMES = [
        [
            "  **     **  ",
            " ****   **** ",
            "****** ******",
            "*************",
            " *********** ",
            "  *********  ",
            "    *****    ",
            "     ***     ",
            "      *      ",
        ],
        [
            "   **   **   ",
            "  **** ****  ",
            " *********** ",
            "*************",
            " *********** ",
            "  *********  ",
            "    *****    ",
            "     ***     ",
            "      *      ",
        ],
        [
            "   *** ***   ",
            "  *********  ",
            "*************",
            "*************",
            " *********** ",
            "  *********  ",
            "    *****    ",
            "     ***     ",
            "      *      ",
        ],
        [
            "  **     **  ",
            " ****   **** ",
            "****** ******",
            "*************",
            " *********** ",
            "  *********  ",
            "    *****    ",
            "     ***     ",
            "      *      ",
        ],
    ]

    def compose(self) -> ComposeResult:
        with Container(classes="valentine-modal"):
            with Container(id="dialog"):
                yield Static(
                    pad_lines("\n".join(self.HEART_FRAMES[0]), 9),
                    id="heart",
                    classes="fill-text",
                )
                yield Static(
                    pad_lines("WILL YOU BE MY VALENTINE BUBS?  ❤", 5),
                    id="valentine-title",
                    classes="fill-text",
                )
                with Horizontal(id="valentine-buttons"):
                    yield Button("Yes", id="yes", variant="primary")
                    yield Button("Also Yes", id="also-yes")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()

    def on_mount(self) -> None:
        self._frame = 0
        self._heart = self.query_one("#heart", Static)
        self.set_interval(0.3, self._animate_heart)

    def _animate_heart(self) -> None:
        self._frame = (self._frame + 1) % len(self.HEART_FRAMES)
        frame = "\n".join(self.HEART_FRAMES[self._frame])
        self._heart.update(pad_lines(frame, 9))


if __name__ == "__main__":
    Game2048().run()
