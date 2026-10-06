from __future__ import annotations

import time
from collections.abc import Iterator

import pygame

from pathfinder.algorithms import ALGORITHMS, Step, path_cost
from pathfinder.grid import HEAVY_WEIGHT, Cell, Grid
from pathfinder.maze import generate_maze, random_walls

ROWS, COLS = 33, 49
CELL = 20
PANEL_W = 290
WIDTH, HEIGHT = COLS * CELL + PANEL_W, ROWS * CELL

COLORS = {
    "bg": (15, 23, 42),
    "panel": (17, 24, 39),
    "grid_line": (30, 41, 59),
    "empty": (241, 245, 249),
    "wall": (30, 41, 59),
    "weight": (203, 213, 225),
    "visited_a": (56, 189, 248),
    "visited_b": (129, 140, 248),
    "frontier": (167, 243, 208),
    "path": (251, 191, 36),
    "start": (34, 197, 94),
    "end": (239, 68, 68),
    "text": (226, 232, 240),
    "muted": (148, 163, 184),
    "accent": (56, 189, 248),
}

SPEEDS = [1, 2, 5, 10, 25, 60]  # search steps per frame

KEYS_HELP = [
    ("1-5", "choose algorithm"),
    ("Space", "run / pause"),
    ("L-click", "draw walls / move S, E"),
    ("R-click", "erase"),
    ("W + click", "add weight (cost 5)"),
    ("M", "generate maze"),
    ("N", "random walls"),
    ("R", "reset search"),
    ("C", "clear board"),
    ("+ / -", "speed"),
]


class App:
    def __init__(self, screen: pygame.Surface | None = None) -> None:
        pygame.init()
        pygame.display.set_caption("Pathfinding Visualizer")
        self.screen = screen or pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("segoeui,helvetica,arial", 16)
        self.font_bold = pygame.font.SysFont("segoeui,helvetica,arial", 18, bold=True)
        self.font_title = pygame.font.SysFont("segoeui,helvetica,arial", 24, bold=True)

        self.grid = Grid(ROWS, COLS, start=(ROWS // 2, 6), end=(ROWS // 2, COLS - 7))
        self.algorithm_names = list(ALGORITHMS)
        self.algorithm = self.algorithm_names[0]
        self.speed_index = 3

        self.search: Iterator[Step] | None = None
        self.step: Step | None = None
        self.order: dict[Cell, int] = {}
        self.path_shown = 0
        self.running = False
        self.elapsed_ms = 0.0

        self.dragging: str | None = None  # "start", "end", "wall", "erase", "weight"

    # ---------- search control ----------

    def reset_search(self) -> None:
        self.search = None
        self.step = None
        self.order.clear()
        self.path_shown = 0
        self.running = False
        self.elapsed_ms = 0.0

    def start_search(self) -> None:
        self.reset_search()
        self.search = ALGORITHMS[self.algorithm](self.grid)
        self.running = True

    def advance(self, steps: int) -> None:
        if not self.running or self.search is None:
            return
        t0 = time.perf_counter()
        for _ in range(steps):
            try:
                self.step = next(self.search)
            except StopIteration:
                self.running = False
                break
            if self.step.current is not None and self.step.current not in self.order:
                self.order[self.step.current] = len(self.order)
            if self.step.done:
                self.running = False
                break
        self.elapsed_ms += (time.perf_counter() - t0) * 1000

    @property
    def finished(self) -> bool:
        return self.step is not None and self.step.done

    # ---------- input ----------

    def cell_at(self, pos: tuple[int, int]) -> Cell | None:
        x, y = pos
        if x >= COLS * CELL or y >= ROWS * CELL:
            return None
        return (y // CELL, x // CELL)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN:
            return self.handle_key(event)
        if event.type == pygame.MOUSEBUTTONDOWN:
            cell = self.cell_at(event.pos)
            if cell is None:
                return True
            if event.button == 1:
                if cell == self.grid.start:
                    self.dragging = "start"
                elif cell == self.grid.end:
                    self.dragging = "end"
                elif pygame.key.get_pressed()[pygame.K_w]:
                    self.dragging = "weight"
                else:
                    self.dragging = "wall"
            elif event.button == 3:
                self.dragging = "erase"
            self.apply_drag(cell)
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = None
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            cell = self.cell_at(event.pos)
            if cell is not None:
                self.apply_drag(cell)
        return True

    def apply_drag(self, cell: Cell) -> None:
        if self.running:
            return
        g = self.grid
        if self.dragging == "start" and cell != g.end and g.passable(cell):
            g.start = cell
        elif self.dragging == "end" and cell != g.start and g.passable(cell):
            g.end = cell
        elif self.dragging == "wall":
            g.toggle_wall(cell, on=True)
        elif self.dragging == "erase":
            g.toggle_wall(cell, on=False)
        elif self.dragging == "weight":
            g.set_weight(cell, HEAVY_WEIGHT)
        if self.step is not None:
            self.reset_search()

    def handle_key(self, event: pygame.event.Event) -> bool:
        key = event.key
        if key == pygame.K_ESCAPE:
            return False
        if pygame.K_1 <= key <= pygame.K_9:
            index = key - pygame.K_1
            if index < len(self.algorithm_names):
                self.algorithm = self.algorithm_names[index]
                self.reset_search()
        elif key == pygame.K_SPACE:
            if self.search is None or self.finished:
                self.start_search()
            else:
                self.running = not self.running
        elif key == pygame.K_r:
            self.reset_search()
        elif key == pygame.K_c:
            self.reset_search()
            self.grid.clear()
        elif key == pygame.K_m:
            self.reset_search()
            generate_maze(self.grid)
        elif key == pygame.K_n:
            self.reset_search()
            random_walls(self.grid)
        elif key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
            self.speed_index = min(self.speed_index + 1, len(SPEEDS) - 1)
        elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.speed_index = max(self.speed_index - 1, 0)
        return True

    # ---------- drawing ----------

    def visited_color(self, index: int) -> tuple[int, int, int]:
        total = max(len(self.order), 1)
        t = index / total
        a, b = COLORS["visited_a"], COLORS["visited_b"]
        return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

    def draw_grid(self) -> None:
        g = self.grid
        frontier = self.step.frontier if self.step and not self.step.done else set()
        path = self.step.path[: self.path_shown] if self.finished else []
        path_set = set(path)

        for r in range(g.rows):
            for c in range(g.cols):
                cell = (r, c)
                rect = pygame.Rect(c * CELL, r * CELL, CELL, CELL)
                if cell in g.walls:
                    color = COLORS["wall"]
                elif cell in path_set:
                    color = COLORS["path"]
                elif cell in self.order:
                    color = self.visited_color(self.order[cell])
                elif cell in frontier:
                    color = COLORS["frontier"]
                elif cell in g.weights:
                    color = COLORS["weight"]
                else:
                    color = COLORS["empty"]
                pygame.draw.rect(self.screen, color, rect)
                if cell in g.weights and cell not in g.walls:
                    pygame.draw.circle(self.screen, COLORS["wall"], rect.center, 3)
                pygame.draw.rect(self.screen, COLORS["grid_line"], rect, 1)

        for cell, key in ((g.start, "start"), (g.end, "end")):
            rect = pygame.Rect(cell[1] * CELL - 2, cell[0] * CELL - 2, CELL + 4, CELL + 4)
            pygame.draw.rect(self.screen, (255, 255, 255), rect, border_radius=6)
            pygame.draw.rect(self.screen, COLORS[key], rect.inflate(-6, -6), border_radius=4)

    def text(self, value: str, pos: tuple[int, int], font=None, color: str = "text") -> None:
        surface = (font or self.font).render(value, True, COLORS[color])
        self.screen.blit(surface, pos)

    def draw_panel(self) -> None:
        x0 = COLS * CELL
        pygame.draw.rect(self.screen, COLORS["panel"], (x0, 0, PANEL_W, HEIGHT))
        x = x0 + 20
        y = 18
        self.text("Pathfinding", (x, y), self.font_title)
        y += 42

        self.text("ALGORITHM", (x, y), self.font, "muted")
        y += 24
        for i, name in enumerate(self.algorithm_names):
            selected = name == self.algorithm
            if selected:
                pygame.draw.rect(self.screen, (30, 58, 95), (x - 8, y - 2, PANEL_W - 24, 24), border_radius=6)
            self.text(f"{i + 1}  {name}", (x, y), self.font_bold if selected else self.font,
                      "accent" if selected else "text")
            y += 26
        y += 10

        self.text("STATS", (x, y), self.font, "muted")
        y += 24
        if self.finished:
            status = "Path found" if self.step.path else "No path"
        elif self.running:
            status = "Searching..."
        elif self.search is not None:
            status = "Paused"
        else:
            status = "Ready"
        path = self.step.path if self.finished else []
        rows = [
            ("Status", status),
            ("Visited", str(len(self.order))),
            ("Path length", str(max(len(path) - 1, 0)) if path else "-"),
            ("Path cost", str(path_cost(self.grid, path)) if path else "-"),
            ("Time", f"{self.elapsed_ms:.1f} ms"),
            ("Speed", f"{SPEEDS[self.speed_index]} steps/frame"),
        ]
        for label, value in rows:
            self.text(label, (x, y), self.font, "muted")
            self.text(value, (x + 110, y))
            y += 22
        y += 12

        self.text("CONTROLS", (x, y), self.font, "muted")
        y += 24
        for key, desc in KEYS_HELP:
            self.text(key, (x, y), self.font_bold)
            self.text(desc, (x + 96, y), self.font, "muted")
            y += 21

    def draw(self) -> None:
        self.screen.fill(COLORS["bg"])
        self.draw_grid()
        self.draw_panel()

    # ---------- main loop ----------

    def update(self) -> None:
        self.advance(SPEEDS[self.speed_index])
        if self.finished and self.path_shown < len(self.step.path):
            self.path_shown += 1

    def run(self) -> None:
        alive = True
        while alive:
            for event in pygame.event.get():
                alive = self.handle_event(event) and alive
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()
