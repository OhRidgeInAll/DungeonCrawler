from dataclasses import dataclass
import random


@dataclass(frozen=True)
class Part:
    """Player equipment parts dropped from defeated enemies, which can be equipped to modify player stats."""
    slot: str            # "arm", "legs", or "core"
    name: str
    modifiers: dict       # stat name -> delta, e.g. {"attack_power": 5}
    source_archetype: str = None


# Which parts a given enemy archetype can drop.
LOOT_TABLE = {
    "grunt": [
        Part("arm", "Grunt Blaster Arm", {"attack_power": 3}, "grunt"),
        Part("legs", "Grunt Servo Legs", {"move_speed": 5}, "grunt"),
        Part("core", "Grunt Plating Core", {"max_health": 15}, "grunt"),
    ],
    "tank": [
        Part("arm", "Tank Cannon Arm", {"attack_power": 8}, "tank"),
        Part("legs", "Tank Tread Legs", {"move_speed": -10, "max_health": 30}, "tank"),
        Part("core", "Tank Armor Core", {"max_health": 40}, "tank"),
    ],
    "sniper": [
        Part("arm", "Sniper Rifle Arm", {"attack_power": 2, "attack_range": 3}, "sniper"),
        Part("legs", "Sniper Recon Legs", {"move_speed": 10}, "sniper"),
        Part("core", "Sniper Optics Core", {"attack_range": 1}, "sniper"),
    ],
}

LOOT_DROP_CHANCE = 0.4


def roll_loot(archetype_id):
    """Maybe return a random Part dropped by the given enemy archetype, or None."""
    table = LOOT_TABLE.get(archetype_id)
    if not table or random.random() > LOOT_DROP_CHANCE:
        return None
    return random.choice(table)
