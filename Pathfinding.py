from typing import List, Tuple, Set, Dict, Optional
import heapq
from constants import *

class AStarPathfinder:
    """A* pathfinding implementation for grid-based dungeons."""
    
    def __init__(self, game_board):
        self.game_board = game_board
    
    def find_path(self, start: Tuple[int, int], goal: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
        """
        Find path from start to goal using A* algorithm.
        Returns list of grid positions from start to goal (excluding start, including goal).
        Returns None if no path exists.
        """
        if not self.game_board.is_position_in_dungeon(*goal):
            return None
        
        if self.game_board.is_position_blocked(*goal):
            return None
        
        # Priority queue: (f_score, counter, position)
        open_set = []
        heapq.heappush(open_set, (0, 0, start))
        
        # Track came_from and g_scores
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        g_score: Dict[Tuple[int, int], float] = {start: 0}
        f_score: Dict[Tuple[int, int], float] = {start: self.heuristic(start, goal)}
        
        counter = 1  # For tie-breaking in heapq
        
        while open_set:
            current_f, _, current = heapq.heappop(open_set)
            
            if current == goal:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return path
            
            for neighbor in self.get_neighbors(current):
                # Calculate tentative g_score
                tentative_g = g_score[current] + self.distance(current, neighbor)
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    # This path to neighbor is better than any previous one
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self.heuristic(neighbor, goal)
                    
                    # Check if neighbor is already in open_set
                    in_open_set = any(pos == neighbor for _, _, pos in open_set)
                    if not in_open_set:
                        heapq.heappush(open_set, (f_score[neighbor], counter, neighbor))
                        counter += 1
        
        # No path found
        return None
    
    def get_neighbors(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get valid neighboring positions (4-directional movement)."""
        x, y = pos
        neighbors = []
        
        # Check all four directions
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = x + dx, y + dy
            
            # Check if position is in dungeon
            if not self.game_board.is_position_in_dungeon(nx, ny):
                continue
            
            # Check if position is blocked
            if self.game_board.is_position_blocked(nx, ny):
                continue
            
            # Don't move through enemies (but allow moving to goal even if occupied?)
            # For now, allow moving through enemies - they'll move on their turn
            neighbors.append((nx, ny))
        
        return neighbors
    
    def distance(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """Cost to move from a to b (Manhattan distance)."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """Heuristic function for A* (Manhattan distance)."""
        return self.distance(a, b)
    
    def find_path_with_vision_check(self, start: Tuple[int, int], goal: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
        """
        Find path but stop if any enemy is within vision range during the path.
        Returns path up to the point before enemy is detected.
        """
        full_path = self.find_path(start, goal)
        if not full_path:
            return None

        safe_path = []
        for step_pos in full_path:
            if self.enemy_in_vision_of(step_pos):
                # Stop path before this step (enemy detected)
                break
            safe_path.append(step_pos)

        return safe_path if safe_path else None

    def enemy_in_vision_of(self, pos: Tuple[int, int]) -> bool:
        """Whether any enemy's own vision_range would cover the given grid position -
        matches Enemy.take_turn()'s own vision gate (range + line-of-sight), so the
        player's auto-walk preview stops in exactly the same cases an enemy would
        actually notice it."""
        for enemy in self.game_board.enemies:
            vision = getattr(enemy, 'vision_range', 5)
            if self.distance(pos, (enemy.grid_x, enemy.grid_y)) <= vision and \
                    self.game_board.has_line_of_sight(enemy.grid_x, enemy.grid_y, pos[0], pos[1]):
                return True
        return False


class MouseController:
    """Handles right-click-to-move: computes a path once, then advances it exactly
    one grid step per resolved turn, stopping early if an enemy comes into vision.

    Previous versions of this scheduled a new invoke() every frame while waiting on
    a turn to resolve, with nothing to stop those from stacking up - dozens could
    fire back-to-back, each popping another step off the path regardless of whether
    the prior step's turn had actually finished, causing the player to warp through
    several waypoints at once. `_step_scheduled` below is the fix: only one pending
    step is ever allowed in flight at a time.
    """

    STEP_DELAY = 0.15  # brief pause after a turn resolves before taking the next step

    def __init__(self, game_board):
        self.game_board = game_board
        self.pathfinder = AStarPathfinder(game_board)
        self.path: List[Tuple[int, int]] = []
        self.active = False
        self._step_scheduled = False
        self._pending_step = None  # the Sequence returned by invoke(), so stop() can cancel it

    def on_right_click(self, world_pos):
        """Handle right-click to move player to clicked position."""
        grid_x, grid_y = world_to_grid(world_pos)

        if not self.game_board.is_position_in_dungeon(grid_x, grid_y):
            print(f"Position ({grid_x}, {grid_y}) not in dungeon")
            return

        if self.game_board.is_position_blocked(grid_x, grid_y):
            print(f"Position ({grid_x}, {grid_y}) is blocked")
            return

        player_pos = self.game_board.player.grid_position
        path = self.pathfinder.find_path_with_vision_check(player_pos, (grid_x, grid_y))

        if not path:
            print("No valid path found")
            self.stop()
            return

        print(f"Path found with {len(path)} steps")
        self.path = path
        self.active = True
        # Take the first step immediately for responsiveness, unless a turn is already
        # resolving - process_turn() would just no-op and silently drop this step, so
        # let update()'s turn_in_progress-guarded scheduling pick it up once it clears.
        if not self.game_board.turn_in_progress:
            self._advance()

    def stop(self):
        """Cancel any in-progress auto-walk, including a step already scheduled via invoke()."""
        self.active = False
        self.path = []
        self._step_scheduled = False
        if self._pending_step is not None:
            self._pending_step.kill()
            self._pending_step = None

    def _advance(self):
        """Take exactly one step of the path, if it's still safe to do so."""
        if not self.active or not self.path:
            self.stop()
            return

        next_pos = self.path.pop(0)

        if self.pathfinder.enemy_in_vision_of(next_pos):
            self.stop()
            return

        self.game_board.queue_player_action('move', next_pos[0], next_pos[1])
        self.game_board.process_turn()

        if not self.path:
            self.stop()

    def update(self):
        """Once per frame: if we're auto-walking and the last turn has resolved,
        schedule exactly one more step (never more than one pending at a time)."""
        if not self.active or self.game_board.turn_in_progress or self._step_scheduled:
            return

        self._step_scheduled = True
        self._pending_step = invoke(self._scheduled_advance, delay=self.STEP_DELAY)

    def _scheduled_advance(self):
        self._step_scheduled = False
        self._pending_step = None
        self._advance()
