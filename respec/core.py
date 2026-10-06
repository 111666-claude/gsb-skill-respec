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
    for tid, rank in target.items():
        if rank < 1:
            continue
        for req in TALENTS[tid]["requires"]:
            if target.get(req, 0) < 1:
                return "missing-prereq"
    tier_points = {}
    for tid, rank in target.items():
        if rank < 1:
            continue
        talent = TALENTS[tid]
        tier_points[talent["tier"]] = tier_points.get(talent["tier"], 0) + rank * talent["cost"]
    lower = 0
    for tier in sorted(tier_points):
        if tier >= 2 and lower < TIER_STEP * (tier - 1):
            return "tier-gate"
        lower += tier_points[tier]
    return None


def tokens_used(ledger, counter):
    """统计台账里已经用掉的券数。"""
    used = 0
    for entry in ledger:
        counter.scanned += 1
        if entry.get("used_token"):
            used += 1
    return used


def _tokens_used(state, counter):
    """优先读缓存的已用券数，没有缓存才扫台账。"""
    if "tokens_used" in state:
        return state["tokens_used"]
    return tokens_used(state["ledger"], counter)


def _tokens_left(state, counter):
    return state["tokens_total"] - _tokens_used(state, counter)


def plan(state, target, req_id, counter):
    """算一遍重置结果，不改状态。"""
    left = _tokens_left(state, counter)
    reason = validate(target)
    if reason:
        return {
            "req_id": req_id,
            "status": "invalid",
            "reason": reason,
            "fee": 0,
            "gold_after": state["gold"],
            "tokens_left": left,
            "points": spent_points(state["ranks"]),
            "scanned": counter.scanned,
        }
    fee = FEE_PER_POINT * spent_points(target)
    use_token = left > 0
    if not use_token and state["gold"] - fee < 0:
        return {
            "req_id": req_id,
            "status": "no-funds",
            "reason": None,
            "fee": fee,
            "gold_after": state["gold"],
            "tokens_left": left,
            "points": spent_points(state["ranks"]),
            "scanned": counter.scanned,
        }
    return {
        "req_id": req_id,
        "status": "ok",
        "reason": None,
        "fee": 0 if use_token else fee,
        "gold_after": state["gold"] if use_token else state["gold"] - fee,
        "tokens_left": left - 1 if use_token else left,
        "points": spent_points(target),
        "scanned": counter.scanned,
    }


def apply(state, target, req_id, counter):
    """结算一次重置并把结果落进台账。"""
    index = state.get("index")
    if index is None:
        index = {}
        for pos, entry in enumerate(state["ledger"]):
            counter.scanned += 1
            index[entry["req_id"]] = pos
        state["index"] = index
    pos = index.get(req_id)
    if pos is not None:
        first = state["ledger"][pos].get("result")
        if first is not None:
            out = dict(first)
            out["status"] = "replay"
            out["scanned"] = counter.scanned
            return out
    if "tokens_used" not in state:
        state["tokens_used"] = tokens_used(state["ledger"], counter)
    out = plan(state, target, req_id, counter)
    if out["status"] != "ok":
        return out
    used_token = state["tokens_total"] - state["tokens_used"] > 0
    state["ranks"] = dict(target)
    state["gold"] = out["gold_after"]
    if used_token:
        state["tokens_used"] += 1
    index[req_id] = len(state["ledger"])
    state["ledger"].append({
        "req_id": req_id,
        "fee": out["fee"],
        "used_token": used_token,
        "result": dict(out),
    })
    return out


def status(state):
    return {
        "points": spent_points(state["ranks"]),
        "gold": state["gold"],
        "tokens_left": _tokens_left(state, Counter()),
        "ledger": len(state["ledger"]),
    }
