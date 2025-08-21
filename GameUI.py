from ursina import *

class CombatUI:
    def __init__(self):
        self.health_bar = Entity(
            parent = camera.ui,
            model = 'quad',
            scale = (0.3, 0.05),
            color = color.red,
            position=(-0.7, 0.4))

        self.health_background = Entity(
            parent=self.health_bar,
            model='quad',
            scale=(1.02, 1.1),
            color=color.black,
            z=0.1)

        self.health_text = Text(
            text = "100/100",
            parent = camera.ui,
            position = (0.55, 0.4),
            scale=1.5)

        self.cooldown_indicator = Entity(
            parent = camera.ui,
            model = 'circle',
            scale = 0.03,
            color = color.yellow,
            position = (0.6, 0.4))
    
    def update(self, player):
        # Update health bar
        health_pct = player.health / 100.0
        self.health_bar.scale_x = 0.3 * player.health_pct
        self.health_text.text = f"{player.health}/100"

        if player.attack_cooldown > 0:
            self.cooldown_indicator.color = color.gray
            self.cooldown_indicator.scale = 0.03 * (player.attack_cooldown / ATTACK_COOLDOWN)
        else:
            self.cooldown_indicator.color = color.yellow
            self.cooldown_indicator.scale = 0.03