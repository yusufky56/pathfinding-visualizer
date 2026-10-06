"""Maze generation with a randomized depth-first search (recursive backtracker)."""

from __future__ import annotations

import random

from pathfinder.grid import Cell, Grid


def generate_maze(grid: Grid, rng: random.Random | None = None) -> None:
    """Fill the grid with walls and carve a perfect maze into it.

    Passages live on even (row, col) coordinates; walls between them are
    removed as the generator walks. Start and end are moved onto passages
    so the maze is always solvable.
    """
    rng = rng or random.Random()
    grid.clear()
    grid.walls = {(r, c) for r in range(grid.rows) for c in range(grid.cols)}

    first: Cell = (0, 0)
    grid.walls.discard(first)
    stack = [first]
    while stack:
        r, c = stack[-1]
        options = []
        for dr, dc in ((-2, 0), (0, 2), (2, 0), (0, -2)):
            nxt = (r + dr, c + dc)
            if grid.in_bounds(nxt) and nxt in grid.walls:
                options.append(nxt)
        if not options:
            stack.pop()
            continue
        nr, nc = rng.choice(options)
        grid.walls.discard(((r + nr) // 2, (c + nc) // 2))
        grid.walls.discard((nr, nc))
        stack.append((nr, nc))

    grid.start = _nearest_open(grid, grid.start)
    grid.end = _nearest_open(grid, grid.end)


def _nearest_open(grid: Grid, cell: Cell) -> Cell:
    r, c = cell
    return (r - r % 2, c - c % 2)


def random_walls(grid: Grid, density: float = 0.3, rng: random.Random | None = None) -> None:
    rng = rng or random.Random()
    grid.clear()
    for r in range(grid.rows):
        for c in range(grid.cols):
            if (r, c) not in (grid.start, grid.end) and rng.random() < density:
                grid.walls.add((r, c))
