from typing import Callable, List, Tuple


def _bresenham_cells(x0: int, y0: int, x1: int, y1: int) -> List[Tuple[int, int]]:
    """Integer grid cells from (x0,y0) to (x1,y1) inclusive, via Bresenham's algorithm.
    Each step moves along the dominant axis alone, or diagonally (both axes by one) -
    never more than one cell apart - which is what makes the corner-cut check in
    has_line_of_sight possible."""
    cells = [(x0, y0)]
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    x, y = x0, y0
    x_step = 1 if x1 > x0 else -1
    y_step = 1 if y1 > y0 else -1

    if dx >= dy:
        err = dx
        while x != x1:
            err -= 2 * dy
            if err < 0:
                y += y_step
                err += 2 * dx
            x += x_step
            cells.append((x, y))
    else:
        err = dy
        while y != y1:
            err -= 2 * dx
            if err < 0:
                x += x_step
                err += 2 * dy
            y += y_step
            cells.append((x, y))

    return cells


def has_line_of_sight(x0: int, y0: int, x1: int, y1: int, blocks_los: Callable[[int, int], bool]) -> bool:
    """Whether sight is clear between two grid cells, walking a Bresenham line and
    checking each intermediate cell against blocks_los(x, y).

    blocks_los is injected rather than hardcoded so this stays a pure, unit-testable
    primitive - any future consumer (fog-of-war, a different blocking rule) can reuse
    it with its own predicate instead of this module knowing about GameBoard.

    The start cell is never checked (an actor's own tile can't block its own sight),
    and the destination cell is never checked either (a target isn't rejected just for
    being the target - only cells strictly between the two matter).

    Uses a corner-safe walk: naive Bresenham can step diagonally through the shared
    corner of two blocking cells without ever occupying either of them. Whenever a step
    is diagonal, both orthogonal "corner" cells are checked, and the step only counts as
    blocked if BOTH of them block sight - matching the standard no-corner-cutting rule.
    """
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    if x0 == x1 and y0 == y1:
        return True

    cells = _bresenham_cells(x0, y0, x1, y1)
    prev_x, prev_y = cells[0]

    for cx, cy in cells[1:]:
        is_destination = (cx == x1 and cy == y1)

        if cx != prev_x and cy != prev_y:
            # Diagonal step: blocked only if both corner cells block sight, so a
            # single-cell-wide diagonal gap between two walls still lets sight through.
            if blocks_los(prev_x, cy) and blocks_los(cx, prev_y):
                return False

        if is_destination:
            return True

        if blocks_los(cx, cy):
            return False

        prev_x, prev_y = cx, cy

    return True
