"""固定场景，用来复现题面里的锚点。"""

import json

from . import core


def _line(obj):
    print(json.dumps(obj, ensure_ascii=False))


def _state(**kw):
    state = {"gold": 500, "tokens_total": 0, "ranks": {}, "ledger": []}
    state.update(kw)
    return state


def run(name):
    if name == "tier":
        state = _state(ranks={"fireball": 3, "flame_ward": 2})
        target = core.build_target({"fireball": 3, "flame_ward": 2, "inferno": 1})
        _line(core.plan(state, target, "tier-1", core.Counter()))
        return 0
    if name == "prereq":
        state = _state(ranks={"fireball": 3})
        target = core.build_target({"fireball": 3, "ice_nova": 1})
        _line(core.plan(state, target, "prereq-1", core.Counter()))
        return 0
    if name == "token":
        state = _state(gold=100, tokens_total=1, ranks={"fireball": 2})
        target = core.build_target({"fireball": 1})
        _line(core.apply(state, target, "tok-1", core.Counter()))
        return 0
    if name == "replay":
        state = _state(gold=500)
        _line(core.apply(state, core.build_target({"fireball": 1}), "r-1", core.Counter()))
        _line(core.apply(state, core.build_target({"fireball": 2}), "r-1", core.Counter()))
        return 0
    if name == "work":
        state = _state(gold=10 ** 9)
        counter = core.Counter()
        target = core.build_target({"fireball": 3})
        for i in range(2000):
            core.apply(state, target, "w-%d" % i, counter)
        _line({"applies": 2000, "scanned": counter.scanned})
        return 0
    raise SystemExit("未知场景：" + name)
