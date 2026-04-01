from ursina import *
from constants import *
from Actor import Actor
import random

class Enemy(Actor):
    def __init__(self, grid_x, grid_y, game_board):
        super().__init__(
            model='quad',
            color=color.red,
            scale=(TILE_SIZE * 0.8, TILE_SIZE * 0.8),
            position = grid_to_world(grid_x, grid_y),
            team = 1
        )
        self.grid_x = grid_x  # Integer grid column
        self.grid_y = grid_y  # Integer grid row
        self.game_board = game_board
        self.move_cooldown = 0
        self.attack_power = random.randint(6, 10)
        self.move_speed = 30  # Slower than player
        self.target_position = self.position
        self.is_moving = False
        self.vision_range = 5  # cells
        
        # Enemy stats variation until enemy types
        self.health = random.randint(60, 100)
        self.attack_power = random.randint(6, 10)
        
        #self.on_death = Death Behaviour Goes Here
    
    def update(self):
        super().update()
        if self.is_moving:
            self.position = lerp(self.position, self.target_position, time.dt * self.move_speed)
            if (self.position - self.target_position).length() < 0.01:
                self.position = self.target_position
                self.is_moving = False
    
    def take_turn(self):
        """Enemy takes a turn: move toward player if in range, otherwise wait."""
        player = self.game_board.player
        if not player:
            return
            
        # Check if player visible (Manhattan dist)
        distance = abs(self.grid_x - player.grid_x) + abs(self.grid_y - player.grid_y)
        if distance <= self.vision_range:
            self.move_toward_player(player.grid_x, player.grid_y)
            
            # Check attack valid
            if self.can_attack_player(player.grid_x, player.grid_y):
                # For now, mark opportunity
                print(f"Enemy at ({self.grid_x},{self.grid_y}) could attack player")
        else:
            # Player not in range, maybe random movement or wait
            pass
    
    def move_toward_player(self, player_x, player_y):
        """Simple AI: move one step toward player if possible."""
        # Calculate direction
        dx = player_x - self.grid_x
        dy = player_y - self.grid_y
        
        # Currently prefer horizontal movement if distance greater otherwise vertical, in future would like to handle paths determined by efficiency once tile types implemented.
        if abs(dx) > abs(dy):
            if dx > 0 and self.can_move_to(self.grid_x + 1, self.grid_y):
                self.move_to_grid_position(self.grid_x + 1, self.grid_y)
            elif dx < 0 and self.can_move_to(self.grid_x - 1, self.grid_y):
                self.move_to_grid_position(self.grid_x - 1, self.grid_y)
            elif dy > 0 and self.can_move_to(self.grid_x, self.grid_y + 1):
                self.move_to_grid_position(self.grid_x, self.grid_y + 1)
            elif dy < 0 and self.can_move_to(self.grid_x, self.grid_y - 1):
                self.move_to_grid_position(self.grid_x, self.grid_y - 1)
        else:
            if dy > 0 and self.can_move_to(self.grid_x, self.grid_y + 1):
                self.move_to_grid_position(self.grid_x, self.grid_y + 1)
            elif dy < 0 and self.can_move_to(self.grid_x, self.grid_y - 1):
                self.move_to_grid_position(self.grid_x, self.grid_y - 1)
            elif dx > 0 and self.can_move_to(self.grid_x + 1, self.grid_y):
                self.move_to_grid_position(self.grid_x + 1, self.grid_y)
            elif dx < 0 and self.can_move_to(self.grid_x - 1, self.grid_y):
                self.move_to_grid_position(self.grid_x - 1, self.grid_y)
    
    def move_to_grid_position(self, x, y):
        """Move enemy to grid position with animation."""
        if self.can_move_to(x, y):
            self.grid_x = x
            self.grid_y = y
            self.target_position = grid_to_world(x, y)
            self.is_moving = True
            return True
        return False
    
    def can_move_to(self, x, y):
        """Check if enemy can move to position."""
        if not self.game_board.is_position_in_dungeon(x, y):
            return False
        
        # Don't path into blocked tiles
        if self.game_board.is_position_blocked(x, y):
            return False
        
        # Don't overlap enemies
        for enemy in self.game_board.enemies:
            if enemy != self and enemy.grid_x == x and enemy.grid_y == y:
                return False
        
        # Don't overlap player
        player = self.game_board.player
        if player and x == player.grid_x and y == player.grid_y:
            return False
        
        return True
    
    def can_attack_player(self, player_x, player_y):
        """Check if enemy can attack player from current position."""
        distance = abs(self.grid_x - player_x) + abs(self.grid_y - player_y)
        return distance <= 1  # Adjacent tiles for melee attack
    
    @property
    def grid_position(self):
        return (self.grid_x, self.grid_y)
