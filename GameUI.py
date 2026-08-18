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
            z=1  # z-fighting fix
        )
        
        self.health_bar = Entity(
            parent=self.health_background,
            model='quad',
            scale=(0.98, 0.8),
            color=color.red,
            origin=(-0.5, 0),  # left-justify
            position=(-0.5, 0, 0),  # flush with the background's left edge
            z=-0.1  # z-fighting fix
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
            color=color.rgba32(0, 0, 0, 150),
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

    def set_visible(self, visible):
        """Show/hide the whole HUD - 
        used for beginning or ending game session since CombatUI is constructed once and reused across sessions"""
        self.health_background.enabled = visible
        self.health_text.enabled = visible
        self.attack_status.enabled = visible
        self.turn_text.enabled = visible
        self.range_indicator.enabled = visible
        self.equipment_text.enabled = visible
        self.floor_text.enabled = visible
        self.minimap_background.enabled = visible
        self.minimap_player_marker.enabled = visible
        for entity in self.minimap_room_entities:
            entity.enabled = visible

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


class InventoryScreen:
    """Dedicated pause-accessible inventory screen with clickable equip/unequip,
    separate from CombatUI's always-on corner panel (which stays as the fast
    at-a-glance/number-key view during normal play)."""

    EQUIPMENT_SLOTS = ("arm", "legs", "core")
    ROW_HEIGHT = 0.07
    MIN_ROW_Y = -0.35

    def __init__(self, on_close):
        self.on_close = on_close
        self.player = None
        self.visible = False
        self.dynamic_entities = []

        self.background = Entity(
            parent=camera.ui,
            model='quad',
            scale=(1.2, 1.0),
            color=color.rgba32(10, 10, 15, 240),
            position=(0, 0),
            z=1,  # z-fighting fix
            enabled=False
        )
        self.title = Text(
            parent=camera.ui,
            text="INVENTORY",
            position=(0, 0.42),
            scale=2.2,
            color=color.white,
            origin=(0, 0),
            enabled=False,
            z=0
        )
        self.close_button = Button(
            parent=camera.ui,
            text="Close",
            position=(0, -0.42),
            scale=(0.25, 0.08),
            color=color.gray,
            on_click=self._handle_close,
            enabled=False,
            z=0
        )

    def show(self, player):
        self.player = player
        self.visible = True
        self.background.enabled = True
        self.title.enabled = True
        self.close_button.enabled = True
        self.refresh()

    def hide(self):
        self.visible = False
        self.background.enabled = False
        self.title.enabled = False
        self.close_button.enabled = False
        self._clear_dynamic()

    def _handle_close(self):
        self.hide()
        if self.on_close:
            self.on_close()

    def _clear_dynamic(self):
        for entity in self.dynamic_entities:
            destroy(entity)
        self.dynamic_entities = []

    def refresh(self):
        """Rebuild the equipped-slot and inventory rows from current player state."""
        self._clear_dynamic()
        if self.player is None:
            return

        y = 0.3
        for slot in self.EQUIPMENT_SLOTS:
            part = self.player.equipment.get(slot)
            self.dynamic_entities.append(Text(
                parent=camera.ui,
                text=f"{slot.capitalize()}: {part.name if part else '(empty)'}",
                position=(-0.5, y),
                scale=1.3,
                color=color.white,
                origin=(-0.5, 0),
                z=0
            ))
            if part is not None:
                self.dynamic_entities.append(Button(
                    parent=camera.ui,
                    text="Unequip",
                    position=(0.35, y),
                    scale=(0.2, 0.06),
                    color=color.orange,
                    on_click=Func(self._unequip, slot),
                    z=0
                ))
            y -= self.ROW_HEIGHT

        y -= 0.05
        self.dynamic_entities.append(Text(
            parent=camera.ui,
            text="Inventory:",
            position=(-0.5, y),
            scale=1.3,
            color=color.yellow,
            origin=(-0.5, 0),
            z=0
        ))
        y -= self.ROW_HEIGHT

        if not self.player.inventory:
            self.dynamic_entities.append(Text(
                parent=camera.ui,
                text="(empty)",
                position=(-0.5, y),
                scale=1.1,
                color=color.gray,
                origin=(-0.5, 0),
                z=0
            ))
        else:
            for part in list(self.player.inventory):
                if y < self.MIN_ROW_Y:
                    break  # keep it on-screen; a scrollable list is future work
                self.dynamic_entities.append(Text(
                    parent=camera.ui,
                    text=f"{part.name} ({part.slot})",
                    position=(-0.5, y),
                    scale=1.1,
                    color=color.white,
                    origin=(-0.5, 0),
                    z=0
                ))
                self.dynamic_entities.append(Button(
                    parent=camera.ui,
                    text="Equip",
                    position=(0.35, y),
                    scale=(0.2, 0.06),
                    color=color.lime,
                    on_click=Func(self._equip, part),
                    z=0
                ))
                y -= self.ROW_HEIGHT

    def _equip(self, part):
        self.player.equip(part)
        self.refresh()

    def _unequip(self, slot):
        self.player.unequip(slot)
        self.refresh()
