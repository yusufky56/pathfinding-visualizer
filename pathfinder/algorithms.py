"""Search algorithms written as generators.

Each algorithm yields a `Step` every time it expands a node, so the UI can
animate the search one step at a time. When the search ends, the last step
has `done=True` and carries the final path (empty if no path exists).
"""

from __future__ import annotations

import heapq
from collections import deque
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field

from pathfinder.grid import Cell, Grid


@dataclass
class Step:
    current: Cell | None
    visited: set[Cell]
    frontier: set[Cell]
    done: bool = False
    path: list[Cell] = field(default_factory=list)


def reconstruct(came_from: dict[Cell, Cell | None], end: Cell) -> list[Cell]:
    if end not in came_from:
        return []
    path = [end]
    while (prev := came_from[path[-1]]) is not None:
        path.append(prev)
    path.reverse()
    return path


def path_cost(grid: Grid, path: list[Cell]) -> int:
    return sum(grid.cost(cell) for cell in path[1:])


def manhattan(a: Cell, b: Cell) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def bfs(grid: Grid) -> Iterator[Step]:
    came_from: dict[Cell, Cell | None] = {grid.start: None}
    queue = deque([grid.start])
    visited: set[Cell] = set()

    while queue:
        current = queue.popleft()
        visited.add(current)
        if current == grid.end:
            break
        for nxt in grid.neighbors(current):
            if nxt not in came_from:
                came_from[nxt] = current
                queue.append(nxt)
        yield Step(current, visited, set(queue))

    yield Step(None, visited, set(), done=True, path=reconstruct(came_from, grid.end))


def dfs(grid: Grid) -> Iterator[Step]:
    came_from: dict[Cell, Cell | None] = {grid.start: None}
    stack = [grid.start]
    visited: set[Cell] = set()

    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        if current == grid.end:
            break
        for nxt in reversed(list(grid.neighbors(current))):
            if nxt not in visited:
                came_from[nxt] = current
                stack.append(nxt)
        yield Step(current, visited, set(stack))

    path = reconstruct(came_from, grid.end) if grid.end in visited else []
    yield Step(None, visited, set(), done=True, path=path)


def _best_first(grid: Grid, heuristic: Callable[[Cell], int]) -> Iterator[Step]:
    """Shared core of Dijkstra (heuristic = 0) and A*."""
    came_from: dict[Cell, Cell | None] = {grid.start: None}
    g_score: dict[Cell, int] = {grid.start: 0}
    # Heap entries: (f = g + h, h, insertion order, cell). Ties on f are broken
    # by the smaller h, which keeps A* heading toward the goal on open ground.
    counter = 0
    start_h = heuristic(grid.start)
    heap: list[tuple[int, int, int, Cell]] = [(start_h, start_h, counter, grid.start)]
    visited: set[Cell] = set()

    while heap:
        *_, current = heapq.heappop(heap)
        if current in visited:
            continue
        visited.add(current)
        if current == grid.end:
            break
        for nxt in grid.neighbors(current):
            new_g = g_score[current] + grid.cost(nxt)
            if new_g < g_score.get(nxt, float("inf")):
                g_score[nxt] = new_g
                came_from[nxt] = current
                counter += 1
                h = heuristic(nxt)
                heapq.heappush(heap, (new_g + h, h, counter, nxt))
        frontier = {entry[-1] for entry in heap if entry[-1] not in visited}
        yield Step(current, visited, frontier)

    yield Step(None, visited, set(), done=True, path=reconstruct(came_from, grid.end))


def dijkstra(grid: Grid) -> Iterator[Step]:
    return _best_first(grid, lambda _: 0)


def astar(grid: Grid) -> Iterator[Step]:
    return _best_first(grid, lambda cell: manhattan(cell, grid.end))


def greedy(grid: Grid) -> Iterator[Step]:
    """Greedy best-first: only the heuristic matters, fast but not optimal."""
    came_from: dict[Cell, Cell | None] = {grid.start: None}
    counter = 0
    heap: list[tuple[int, int, Cell]] = [(manhattan(grid.start, grid.end), counter, grid.start)]
    visited: set[Cell] = set()

    while heap:
        _, _, current = heapq.heappop(heap)
        if current in visited:
            continue
        visited.add(current)
        if current == grid.end:
            break
        for nxt in grid.neighbors(current):
            if nxt not in came_from:
                came_from[nxt] = current
                counter += 1
                heapq.heappush(heap, (manhattan(nxt, grid.end), counter, nxt))
        yield Step(current, visited, {cell for _, _, cell in heap if cell not in visited})

    yield Step(None, visited, set(), done=True, path=reconstruct(came_from, grid.end))


ALGORITHMS: dict[str, Callable[[Grid], Iterator[Step]]] = {
    "A*": astar,
    "Dijkstra": dijkstra,
    "BFS": bfs,
    "DFS": dfs,
    "Greedy": greedy,
}


def run(algorithm: Callable[[Grid], Iterator[Step]], grid: Grid) -> Step:
    """Run a search to completion and return the final step."""
    last = None
    for last in algorithm(grid):
        pass
    assert last is not None and last.done
    return last
