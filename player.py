from ursina import *
from ursina.prefabs.sprite_sheet_animation import SpriteSheetAnimation
import constants
import random
from Actor import *

ATTACK_ANIMATION_FPS = 8
ATTACK_ANIMATION_FRAMES = 3
ATTACK_ANIMATION_DURATION = ATTACK_ANIMATION_FRAMES / ATTACK_ANIMATION_FPS

class Player(Actor):
    def __init__(self, parent):
        # Position will be set by GameBoard after dungeon generation
        # We're overriding the Entity class to create a Player class
        super().__init__(
            game = parent,
            model=None,  # We'll use sprite sheet instead
            # Position set by gameboard
            position=(0, 0, -0.1),  # Temporary position
            z=-0.1,  # Slightly above the grid
            team=0
            )
        
        # SpriteAnimation setup for player character - idle/walk/attack rows
        self.sprite = SpriteSheetAnimation(
            'assets/Robot.png',
            tileset_size=(4, 3),
            fps=ATTACK_ANIMATION_FPS,
            animations={
                'idle': ((0, 0), (1, 0)),
                'walk': ((0, 1), (3, 1)),
                'attack': ((0, 2), (2, 2)),
            },
            parent=self,
            position=(0, 0, 0),
            scale=(constants.TILE_SIZE * 0.8, constants.TILE_SIZE * 0.8)
        )
        self.sprite_state = 'idle'
        self.sprite.play_animation('idle')
        self.is_attack_animation_playing = False
        self.health = 100
        self.grid_x = 0  # temp, will be set by gameboard (both x,y)
        self.grid_y = 0
        self.target_position = self.position
        self.move_speed = 50
        self.is_moving = False

        # Attack range checking will use distance instead of collider - Impl for ranged weaponry
        self.attack_range = constants.ATTACK_RANGE
        self.has_attacked_this_turn = False

        # Resources - currency has no ceiling, energy is a spendable pool (skills draw from it)
        self.currency = 0
        self.max_energy = constants.STARTING_MAX_ENERGY
        self.energy = self.max_energy

        # Equipment / salvage system - Raw player stats TODO: Attach to stock parts
        self.base_attack_power = self.attack_power
        self.base_attack_range = self.attack_range
        self.base_move_speed = self.move_speed
        self.base_max_health = self.health
        self.base_accuracy = self.accuracy
        self.base_armor = self.armor
        self.base_max_energy = self.max_energy

        self.equipment = {"arm": None, "legs": None, "core": None}
        self.inventory = []
        self._recompute_stats()

        self.on_death = self._on_death

    @property
    def grid_position(self):
        return (self.grid_x, self.grid_y)

    def _on_death(self):
        """Flag the board so main.py stops touching this (now-destroyed) entity instead
        of crashing on the next frame. A real Game Over screen is iteration 8's job,
        once the menu/game-state machine exists to transition into."""
        if hasattr(self, 'game') and self.game:
            self.game.player_defeated = True
            print("[GAME OVER] Player defeated.")

    def equip(self, part):
        """Swap/Equip a salvaged part from the inventory, returning any part it replaces to the inventory."""
        if part not in self.inventory:
            return False

        previous = self.equipment.get(part.slot)
        self.inventory.remove(part)
        if previous is not None:
            self.inventory.append(previous)
        self.equipment[part.slot] = part
        self._recompute_stats()
        return True

    def unequip(self, slot):
        """Move the part equipped in the given slot back to the inventory."""
        part = self.equipment.get(slot)
        if part is None:
            return False

        self.equipment[slot] = None
        self.inventory.append(part)
        self._recompute_stats()
        return True

    def _recompute_stats(self):
        """Recalculate effective stats from base stats plus all equipped part modifiers."""
        attack_power = self.base_attack_power
        attack_range = self.base_attack_range
        move_speed = self.base_move_speed
        max_health = self.base_max_health
        accuracy = self.base_accuracy
        armor = self.base_armor
        max_energy = self.base_max_energy

        for part in self.equipment.values():
            if part is None:
                continue
            attack_power += part.modifiers.get('attack_power', 0)
            attack_range += part.modifiers.get('attack_range', 0)
            move_speed += part.modifiers.get('move_speed', 0)
            max_health += part.modifiers.get('max_health', 0)
            accuracy += part.modifiers.get('accuracy', 0)
            armor += part.modifiers.get('armor', 0)
            max_energy += part.modifiers.get('max_energy', 0)

        self.attack_power = attack_power
        self.attack_range = attack_range
        self.move_speed = move_speed
        self.max_health = max_health
        self.accuracy = accuracy
        self.armor = armor
        self.max_energy = max_energy
        self.health = min(self.health, self.max_health)
        self.energy = min(self.energy, self.max_energy)

    def move_to_grid_position(self, x, y):
        if not self.is_moving and self.can_move_to(x, y):
            # Get bounds for clamp
            if constants.DUNGEON_BOUNDS is not None:
                min_x, min_y, max_x, max_y = constants.DUNGEON_BOUNDS
                x = clamp(x, min_x, max_x)
                y = clamp(y, min_y, max_y)
            else:
                # Fallback to def
                x = clamp(x, 0, constants.DEFAULT_GRID_SIZE - 1)
                y = clamp(y, 0, constants.DEFAULT_GRID_SIZE - 1)

            if (x, y) != (self.grid_x, self.grid_y):
                # Convert grid coordinates to world position
                self.grid_x = x
                self.grid_y = y
                self.target_position = constants.grid_to_world(x, y)
                self.is_moving = True

    def can_move_to(self, x, y):
        if not self.game.is_position_in_dungeon(x, y):
            return False
        
        if self.game.is_position_blocked(x, y):
            return False
        
        # Check if there's an enemy at the target position
        enemy_at_target = self.game.get_enemy_at_position(x, y)
        if enemy_at_target:
            return False  # Can't move into enemy tile
        
        return True

    def can_attack(self, target):
        # There was an attempt to implement cooldowns, shortsighted as they were timebased initially
        """Override Actor.can_attack to include turn-based check."""
        # Check if already attacked this turn
        if hasattr(self, 'has_attacked_this_turn') and self.has_attacked_this_turn:
            return False
        
        # Use parent's can_attack for other checks (distance, team, etc.)
        return super().can_attack(target)
    
    def attack(self, target):
        """Override Actor.attack to set turn-based flag instead of cooldown."""
        if self.can_attack(target):
            # Get target position before potentially destroying it
            target_position = target.position if hasattr(target, 'position') else None
            # An attack attempt costs the turn either way, hit or miss.
            self.has_attacked_this_turn = True

            if random.random() < self.accuracy:
                dealt = target.take_damage(self.attack_power)
                self.show_attack_effect(target, target_position, damage=dealt)
            else:
                self.show_attack_effect(target, target_position, damage=None)

            self._play_attack_animation()
            return True
        return False
    
    def try_attack(self):
        """Attack the first legal target among game.enemies. Legality (range, team,
        cooldown/turn-flag, line-of-sight) is entirely owned by can_attack() - this
        just selects a candidate, it doesn't re-derive any of those checks itself."""
        if not hasattr(self, 'game') or not self.game.enemies:
            return False

        for enemy in self.game.enemies:
            if self.can_attack(enemy):
                return self.attack(enemy)

        return False

    def try_attack_enemy_at(self, x, y):
        """Try to attack the enemy at a specific grid position, if any. attack() already
        re-checks can_attack() internally, so legality is handled there - no need to
        duplicate it here."""
        if not hasattr(self, 'game') or not self.game.enemies:
            return False

        for enemy in self.game.enemies:
            if enemy.grid_x == x and enemy.grid_y == y:
                return self.attack(enemy)

        return False

    def update(self):
        if self.is_moving:
            self.position = lerp(self.position, self.target_position, time.dt * self.move_speed)

            if (self.position - self.target_position).length() < 0.01:
                self.position = self.target_position
                self.is_moving = False

        if not self.is_attack_animation_playing:
            self._set_sprite_state('walk' if self.is_moving else 'idle')

    def _set_sprite_state(self, state):
        if self.sprite_state != state:
            self.sprite_state = state
            self.sprite.play_animation(state)

    def _play_attack_animation(self):
        self.is_attack_animation_playing = True
        self._set_sprite_state('attack')
        invoke(self._end_attack_animation, delay=ATTACK_ANIMATION_DURATION)

    def _end_attack_animation(self):
        self.is_attack_animation_playing = False
        self._set_sprite_state('walk' if self.is_moving else 'idle')
    
