from ursina import *
from constants import *

class CombatUI:
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
    
    def update(self, player):
        # Update health bar
        health_pct = max(0, player.health / 100.0)
        self.health_bar.scale_x = 0.98 * health_pct
        self.health_text.text = f"{int(player.health)}/100"
        
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
