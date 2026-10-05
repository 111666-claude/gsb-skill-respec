import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from respec import core


def make_state(**kw):
    state = {"gold": 500, "tokens_total": 0, "ranks": {}, "ledger": []}
    state.update(kw)
    return state


class RespecTest(unittest.TestCase):
    def test_apply_replaces_build_and_charges_fee(self):
        state = make_state(ranks={"fireball": 3})
        out = core.apply(state, core.build_target({"fireball": 1}), "r1", core.Counter())
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["fee"], 10)
        self.assertEqual(out["gold_after"], 490)
        self.assertEqual(state["ranks"]["fireball"], 1)
        self.assertEqual(state["ranks"]["frostbolt"], 0)
        self.assertEqual(state["gold"], 490)

    def test_unknown_talent_is_rejected(self):
        state = make_state()
        out = core.apply(state, core.build_target({"nope": 1}), "r2", core.Counter())
        self.assertEqual(out["status"], "invalid")
        self.assertEqual(out["reason"], "unknown-talent")
        self.assertEqual(state["gold"], 500)
        self.assertEqual(state["ledger"], [])

    def test_rank_out_of_range_is_rejected(self):
        state = make_state()
        out = core.plan(state, core.build_target({"fireball": 4}), "r3", core.Counter())
        self.assertEqual(out["status"], "invalid")
        self.assertEqual(out["reason"], "rank-out-of-range")

    def test_plan_does_not_mutate_state(self):
        state = make_state(ranks={"fireball": 3})
        before = json.dumps(state, sort_keys=True)
        core.plan(state, core.build_target({"fireball": 1}), "r4", core.Counter())
        self.assertEqual(json.dumps(state, sort_keys=True), before)

    def test_status_reports_totals(self):
        state = make_state(ranks={"fireball": 2, "frostbolt": 1})
        out = core.status(state)
        self.assertEqual(out["points"], 3)
        self.assertEqual(out["gold"], 500)
        self.assertEqual(out["ledger"], 0)


if __name__ == "__main__":
    unittest.main()
