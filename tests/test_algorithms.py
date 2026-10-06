import random

import pytest

from pathfinder.algorithms import ALGORITHMS, astar, bfs, dfs, dijkstra, greedy, path_cost, run
from pathfinder.grid import Grid
from pathfinder.maze import generate_maze

OPEN = [
    "S.........",
    "..........",
    ".........E",
]

WALLED = [
    "S.#.......",
    "..#.####..",
    "..#....#..",
    "......##.E",
]

BLOCKED = [
    "S.#...",
    "..#..E",
    "..#...",
]

# A cheap detour around an expensive strip in the middle row.
WEIGHTED = [
    "..........",
    "S99999999E",
    "..........",
]


def assert_valid_path(grid: Grid, path: list) -> None:
    assert path[0] == grid.start
    assert path[-1] == grid.end
    for a, b in zip(path, path[1:]):
        assert abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1
        assert grid.passable(b)


@pytest.mark.parametrize("name", list(ALGORITHMS))
@pytest.mark.parametrize("layout", [OPEN, WALLED])
def test_every_algorithm_finds_a_valid_path(name, layout):
    grid = Grid.from_strings(layout)
    result = run(ALGORITHMS[name], grid)
    assert result.done
    assert_valid_path(grid, result.path)


@pytest.mark.parametrize("name", list(ALGORITHMS))
def test_no_path_when_blocked(name):
    grid = Grid.from_strings(BLOCKED)
    assert run(ALGORITHMS[name], grid).path == []


@pytest.mark.parametrize("algorithm", [bfs, dijkstra, astar])
def test_shortest_path_length_unweighted(algorithm):
    grid = Grid.from_strings(WALLED)
    reference = run(bfs, grid).path
    assert len(run(algorithm, grid).path) == len(reference)


def test_open_grid_shortest_is_manhattan_distance():
    grid = Grid.from_strings(OPEN)
    assert len(run(astar, grid).path) - 1 == 2 + 9


def test_weighted_dijkstra_and_astar_avoid_heavy_cells():
    grid = Grid.from_strings(WEIGHTED)
    bfs_cost = path_cost(grid, run(bfs, grid).path)
    dijkstra_cost = path_cost(grid, run(dijkstra, grid).path)
    astar_cost = path_cost(grid, run(astar, grid).path)

    assert dijkstra_cost == astar_cost == 11  # go around: 1 + 8 + ... = 11 steps of cost 1
    assert bfs_cost > dijkstra_cost  # BFS ignores weights


def test_astar_expands_fewer_nodes_than_dijkstra():
    grid = Grid(30, 30, start=(0, 0), end=(29, 29))
    assert len(run(astar, grid).visited) < len(run(dijkstra, grid).visited)


def test_dfs_and_greedy_paths_are_not_shorter_than_optimal():
    grid = Grid.from_strings(WALLED)
    best = len(run(bfs, grid).path)
    assert len(run(dfs, grid).path) >= best
    assert len(run(greedy, grid).path) >= best


def test_steps_are_yielded_before_done():
    grid = Grid.from_strings(OPEN)
    steps = list(astar(grid))
    assert len(steps) > 1
    assert all(not s.done for s in steps[:-1])
    assert steps[-1].done


@pytest.mark.parametrize("seed", range(5))
def test_generated_maze_is_solvable(seed):
    grid = Grid(21, 31, start=(10, 3), end=(10, 27))
    generate_maze(grid, random.Random(seed))
    assert grid.start not in grid.walls
    assert grid.end not in grid.walls
    path = run(bfs, grid).path
    assert_valid_path(grid, path)
    # dfs-based maze: every algorithm agrees on the unique path length
    assert len(run(astar, grid).path) == len(path)
