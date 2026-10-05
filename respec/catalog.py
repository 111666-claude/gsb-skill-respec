"""天赋表。层级按投入深浅排列，cost 是每级消耗的点数。"""

TALENTS = {
    "fireball": {"tier": 1, "max": 3, "cost": 1, "requires": []},
    "frostbolt": {"tier": 1, "max": 3, "cost": 1, "requires": []},
    "arcane_focus": {"tier": 1, "max": 2, "cost": 1, "requires": []},
    "flame_ward": {"tier": 2, "max": 2, "cost": 2, "requires": ["fireball"]},
    "ice_nova": {"tier": 2, "max": 2, "cost": 2, "requires": ["frostbolt"]},
    "inferno": {"tier": 3, "max": 1, "cost": 5, "requires": ["flame_ward"]},
    "arcane_surge": {"tier": 4, "max": 1, "cost": 8, "requires": ["arcane_focus", "ice_nova"]},
}

TIER_STEP = 5
FEE_PER_POINT = 10
