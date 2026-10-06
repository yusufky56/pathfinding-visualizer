from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field

Cell = tuple[int, int]  # (row, col)

WALL = 0
DEFAULT_WEIGHT = 1
HEAVY_WEIGHT = 5


@dataclass
class Grid:
    rows: int
    cols: int
    start: Cell = (0, 0)
    end: Cell = (0, 1)
    walls: set[Cell] = field(default_factory=set)
    weights: dict[Cell, int] = field(default_factory=dict)

    def in_bounds(self, cell: Cell) -> bool:
        r, c = cell
        return 0 <= r < self.rows and 0 <= c < self.cols

    def passable(self, cell: Cell) -> bool:
        return cell not in self.walls

    def cost(self, cell: Cell) -> int:
        """Cost of stepping into `cell`."""
        return self.weights.get(cell, DEFAULT_WEIGHT)

    def neighbors(self, cell: Cell) -> Iterator[Cell]:
        r, c = cell
        for dr, dc in ((-1, 0), (0, 1), (1, 0), (0, -1)):
            nxt = (r + dr, c + dc)
            if self.in_bounds(nxt) and self.passable(nxt):
                yield nxt

    def toggle_wall(self, cell: Cell, on: bool = True) -> None:
        if cell in (self.start, self.end):
            return
        if on:
            self.walls.add(cell)
            self.weights.pop(cell, None)
        else:
            self.walls.discard(cell)
            self.weights.pop(cell, None)

    def set_weight(self, cell: Cell, weight: int = HEAVY_WEIGHT) -> None:
        if cell in (self.start, self.end):
            return
        self.walls.discard(cell)
        self.weights[cell] = weight

    def clear(self) -> None:
        self.walls.clear()
        self.weights.clear()

    @classmethod
    def from_strings(cls, lines: list[str]) -> Grid:
        """Build a grid from text. `S` start, `E` end, `#` wall, digits are weights, `.` empty."""
        grid = cls(rows=len(lines), cols=len(lines[0]))
        for r, line in enumerate(lines):
            for c, ch in enumerate(line):
                if ch == "S":
                    grid.start = (r, c)
                elif ch == "E":
                    grid.end = (r, c)
                elif ch == "#":
                    grid.walls.add((r, c))
                elif ch.isdigit():
                    grid.weights[(r, c)] = int(ch)
        return grid
