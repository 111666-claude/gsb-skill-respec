"""天赋重置的核心判定与台账。"""

from .catalog import TALENTS, TIER_STEP, FEE_PER_POINT


class Counter:
    """记录本轮在台账里检查过的记录条数。"""

    def __init__(self):
        self.scanned = 0


def build_target(sets):
    """把 id=rank 的零散设置补全成一份完整的加点方案（未提到的天赋记 0）。"""
    target = {tid: 0 for tid in TALENTS}
    for tid, rank in (sets or {}).items():
        target[tid] = rank
    return target


def spent_points(ranks):
    total = 0
    for tid, rank in ranks.items():
        talent = TALENTS.get(tid)
        if talent:
            total += rank * talent["cost"]
    return total


def validate(target):
    """返回第一条不满足的原因，全部满足时返回 None。"""
    for tid, rank in target.items():
        talent = TALENTS.get(tid)
        if talent is None:
            return "unknown-talent"
        if rank < 0 or rank > talent["max"]:
            return "rank-out-of-range"
    return None


def tokens_used(ledger, counter):
    """统计台账里已经用掉的券数。"""
    used = 0
    for entry in ledger:
        counter.scanned += 1
        if entry.get("used_token"):
            used += 1
    return used


def _tokens_left(state, counter):
    return state["tokens_total"] - tokens_used(state["ledger"], counter)


def plan(state, target, req_id, counter):
    """算一遍重置结果，不改状态。"""
    reason = validate(target)
    if reason:
        return {
            "req_id": req_id,
            "status": "invalid",
            "reason": reason,
            "fee": 0,
            "gold_after": state["gold"],
            "tokens_left": _tokens_left(state, counter),
            "points": spent_points(state["ranks"]),
            "scanned": counter.scanned,
        }
    fee = FEE_PER_POINT * spent_points(target)
    if state["gold"] - fee < 0:
        return {
            "req_id": req_id,
            "status": "no-funds",
            "reason": None,
            "fee": fee,
            "gold_after": state["gold"],
            "tokens_left": _tokens_left(state, counter),
            "points": spent_points(state["ranks"]),
            "scanned": counter.scanned,
        }
    return {
        "req_id": req_id,
        "status": "ok",
        "reason": None,
        "fee": fee,
        "gold_after": state["gold"] - fee,
        "tokens_left": _tokens_left(state, counter),
        "points": spent_points(target),
        "scanned": counter.scanned,
    }


def apply(state, target, req_id, counter):
    """结算一次重置并把结果落进台账。"""
    out = plan(state, target, req_id, counter)
    if out["status"] != "ok":
        return out
    state["ranks"] = dict(target)
    state["gold"] = out["gold_after"]
    state["ledger"].append({"req_id": req_id, "fee": out["fee"], "used_token": False})
    return out


def status(state):
    return {
        "points": spent_points(state["ranks"]),
        "gold": state["gold"],
        "tokens_left": _tokens_left(state, Counter()),
        "ledger": len(state["ledger"]),
    }
