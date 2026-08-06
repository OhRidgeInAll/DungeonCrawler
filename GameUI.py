from ursina import *
from constants import *

class CombatUI:
    MINIMAP_SIZE = 0.28
    MINIMAP_POSITION = (0.72, -0.32)
    MINIMAP_ROOM_COLORS = {"start": color.lime, "exit": color.gold}

    def __init__(self):
        # Clean HUD layout
        # Health bar at top-left
        self.health_background = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.35, 0.06),
            color=color.black,
            position=(-0.7, 0.45),  # Left side
            z=-1
        )
        
        self.health_bar = Entity(
            parent=self.health_background,
            model='quad',
            scale=(0.98, 0.8),
            color=color.red,
            position=(0, 0, 0),
            z=0
        )
        
        self.health_text = Text(
            text="100/100",
            parent=camera.ui,
            position=(-0.7, 0.45),
            scale=1.8,
            color=color.white,
            origin=(0, 0)
        )
        
        # Attack status indicator
        self.attack_status = Text(
            text="READY",
            parent=camera.ui,
            position=(-0.7, 0.38),
            scale=1.5,
            color=color.green,
            origin=(0, 0)
        )
        
        # Turn counter (top-right)
        self.turn_text = Text(
            text="Turn: 0",
            parent=camera.ui,
            position=(0.75, 0.45),
            scale=1.8,
            color=color.white,
            origin=(0, 0)
        )
        
        # Attack range indicator (top-right)
        self.range_indicator = Text(
            text="Range: 1.5",
            parent=camera.ui,
            position=(0.75, 0.38),
            scale=1.5,
            color=color.yellow,
            origin=(0, 0)
        )

        # Equipment / inventory panel (bottom-left) TODO: Make this a menu either from pause or dockable by keypress
        self.equipment_text = Text(
            text="",
            parent=camera.ui,
            position=(-0.85, -0.2),
            scale=1.1,
            color=color.white,
            origin=(-0.5, 0.5)
        )

        # Floor number (top-right, below the range indicator)
        self.floor_text = Text(
            text="Floor: 1",
            parent=camera.ui,
            position=(0.75, 0.31),
            scale=1.5,
            color=color.cyan,
            origin=(0, 0)
        )

        # Minimap (bottom-right) - room rectangles rebuilt per floor, plus a player marker
        self.minimap_background = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgba(0, 0, 0, 150),
            scale=(self.MINIMAP_SIZE, self.MINIMAP_SIZE),
            position=self.MINIMAP_POSITION,
            z=-1
        )
        self.minimap_room_entities = []
        self.minimap_player_marker = Entity(
            parent=camera.ui,
            model='circle',
            color=color.azure,
            scale=0.015,
            position=(self.MINIMAP_POSITION[0], self.MINIMAP_POSITION[1], -2)
        )

    def _minimap_point(self, normalized_x, normalized_y):
        """Map a 0..1 normalized dungeon-space point to a camera.ui position inside the minimap box."""
        return (
            self.MINIMAP_POSITION[0] + (normalized_x - 0.5) * self.MINIMAP_SIZE,
            self.MINIMAP_POSITION[1] + (normalized_y - 0.5) * self.MINIMAP_SIZE,
        )

    def rebuild_minimap(self, rooms, bounds):
        """Rebuild the minimap's room rectangles for a newly generated floor."""
        for entity in self.minimap_room_entities:
            destroy(entity)
        self.minimap_room_entities = []

        min_x, min_y, max_x, max_y = bounds
        span_x = max(1, max_x - min_x + 1)
        span_y = max(1, max_y - min_y + 1)

        for room in rooms:
            rx0, ry0, rx1, ry1 = room.get_bounds()
            left = (rx0 - min_x) / span_x
            right = (rx1 + 1 - min_x) / span_x
            bottom = (ry0 - min_y) / span_y
            top = (ry1 + 1 - min_y) / span_y

            screen_x, screen_y = self._minimap_point((left + right) / 2, (bottom + top) / 2)
            room_entity = Entity(
                parent=camera.ui,
                model='quad',
                color=self.MINIMAP_ROOM_COLORS.get(room.role, color.gray),
                scale=(max((right - left) * self.MINIMAP_SIZE, 0.008),
                       max((top - bottom) * self.MINIMAP_SIZE, 0.008)),
                position=(screen_x, screen_y, -1.5)
            )
            self.minimap_room_entities.append(room_entity)

    def update(self, player):
        # Update health bar
        max_health = getattr(player, 'max_health', 100)
        health_pct = max(0, player.health / max_health) if max_health else 0
        self.health_bar.scale_x = 0.98 * health_pct
        self.health_text.text = f"{int(player.health)}/{int(max_health)}"

        # Update attack status (turn-based)
        if hasattr(player, 'has_attacked_this_turn') and player.has_attacked_this_turn:
            self.attack_status.text = "ATTACKED"
            self.attack_status.color = color.red
        else:
            self.attack_status.text = "READY"
            self.attack_status.color = color.green

        # Update turn counter (if available)
        if hasattr(player, 'game') and hasattr(player.game, 'current_turn'):
            self.turn_text.text = f"Turn: {player.game.current_turn}"

        # Update range indicator
        self.range_indicator.text = f"Range: {getattr(player, 'attack_range', 1.5)}"

        # Update floor number and the minimap's player-position marker
        game = getattr(player, 'game', None)
        if game is not None and hasattr(game, 'floor_number'):
            self.floor_text.text = f"Floor: {game.floor_number}"
        if game is not None and hasattr(game, 'room_generator'):
            min_x, min_y, max_x, max_y = game.room_generator.get_bounds()
            span_x = max(1, max_x - min_x + 1)
            span_y = max(1, max_y - min_y + 1)
            px = (player.grid_x - min_x + 0.5) / span_x
            py = (player.grid_y - min_y + 0.5) / span_y
            marker_x, marker_y = self._minimap_point(px, py)
            self.minimap_player_marker.position = (marker_x, marker_y, -2)

        # Update equipment / inventory panel
        if hasattr(player, 'equipment'):
            lines = ["Equipped:"]
            for slot in ("arm", "legs", "core"):
                part = player.equipment.get(slot)
                lines.append(f"  {slot}: {part.name if part else '-'}")
            lines.append("Inventory (press number to equip):")
            if player.inventory:
                for i, part in enumerate(player.inventory, start=1):
                    lines.append(f"  [{i}] {part.name} ({part.slot})")
            else:
                lines.append("  (empty)")
            self.equipment_text.text = "\n".join(lines)
