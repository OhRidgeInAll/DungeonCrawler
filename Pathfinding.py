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
    
    def find_path_with_vision_check(self, start: Tuple[int, int], goal: Tuple[int, int], 
                                   vision_range: int = 5) -> Optional[List[Tuple[int, int]]]:
        """
        Find path but stop if any enemy is within vision range during the path.
        Returns path up to the point before enemy is detected.
        """
        full_path = self.find_path(start, goal)
        if not full_path:
            return None
        
        # Check each step of the path for enemies in vision
        safe_path = []
        for step_pos in full_path:
            # Check if any enemy is within vision range of this position
            enemy_in_sight = False
            for enemy in self.game_board.enemies:
                dist = self.distance(step_pos, (enemy.grid_x, enemy.grid_y))
                if dist <= vision_range:
                    enemy_in_sight = True
                    break
            
            if enemy_in_sight:
                # Stop path before this step (enemy detected)
                break
            
            safe_path.append(step_pos)
        
        return safe_path if safe_path else None


class MouseController:
    """Handles mouse controls for player movement with pathfinding."""
    
    def __init__(self, game_board):
        self.game_board = game_board
        self.pathfinder = AStarPathfinder(game_board)
        self.current_path: List[Tuple[int, int]] = []
        self.path_index = 0
        self.following_path = False
        
    def on_right_click(self, world_pos):
        """Handle right-click to move player to clicked position."""
        # Convert world position to grid coordinates
        grid_x, grid_y = world_to_grid(world_pos)
        
        # Check if position is valid
        if not self.game_board.is_position_in_dungeon(grid_x, grid_y):
            print(f"Position ({grid_x}, {grid_y}) not in dungeon")
            return
        
        if self.game_board.is_position_blocked(grid_x, grid_y):
            print(f"Position ({grid_x}, {grid_y}) is blocked")
            return
        
        # Get player current position
        player_pos = (self.game_board.player.grid_x, self.game_board.player.grid_y)
        
        # Find path with vision check
        path = self.pathfinder.find_path_with_vision_check(player_pos, (grid_x, grid_y))
        
        if not path:
            print("No valid path found")
            return
        
        print(f"Path found with {len(path)} steps")
        self.current_path = path
        self.path_index = 0
        self.following_path = True
        
        # Start following the path (one step per turn)
        self.follow_next_step()
    
    def follow_next_step(self):
        """Follow the next step in the current path."""
        if not self.following_path or self.path_index >= len(self.current_path):
            self.following_path = False
            return
        
        next_pos = self.current_path[self.path_index]
        self.path_index += 1
        
        # Queue move action and process turn
        self.game_board.queue_player_action('move', next_pos[0], next_pos[1])
        self.game_board.process_turn()
        
        # Check if we should continue (no enemies in vision at next position)
        # The pathfinder already checked this, but we double-check
        enemy_in_sight = False
        for enemy in self.game_board.enemies:
            dist = abs(next_pos[0] - enemy.grid_x) + abs(next_pos[1] - enemy.grid_y)
            if dist <= 5:  # Vision range
                enemy_in_sight = True
                break
        
        if enemy_in_sight or self.path_index >= len(self.current_path):
            # Enemy detected or path complete
            self.following_path = False
        else:
            # Continue following path after current turn completes
            # We'll check in update() if turn is complete
            pass
    
    def update(self):
        """Update mouse controller state."""
        # Continue following path if turn is complete and we're still following
        if self.following_path and not self.game_board.turn_in_progress:
            # Small delay to ensure animations complete
            invoke(self.follow_next_step, delay=0.2)
