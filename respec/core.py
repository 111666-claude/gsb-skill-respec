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
        if rank <= 0:
            continue
        for req in TALENTS[tid]["requires"]:
            if target.get(req, 0) < 1:
                return "missing-prereq"
    tier_points = {}
    for tid, rank in target.items():
        talent = TALENTS[tid]
        tier = talent["tier"]
        tier_points[tier] = tier_points.get(tier, 0) + rank * talent["cost"]
    for tid, rank in target.items():
        if rank <= 0:
            continue
        tier = TALENTS[tid]["tier"]
        if tier < 2:
            continue
        below = sum(pts for t, pts in tier_points.items() if t < tier)
        if below < TIER_STEP * (tier - 1):
            return "tier-locked"
    return None


def tokens_used(state, counter):
    """统计台账里已经用掉的券数。"""
    if "tokens_used" in state:
        return state["tokens_used"]
    used = 0
    for entry in state["ledger"]:
        counter.scanned += 1
        if entry.get("used_token"):
            used += 1
    return used


def _tokens_left(state, counter):
    total = state["tokens_total"]
    if total <= 0:
        return 0
    return total - tokens_used(state, counter)


def _replay(state, req_id, counter):
    """req_id 已结算过时，返回首次结果（状态标成 replay）。"""
    results = state.get("results")
    if not results or req_id not in results:
        return None
    out = dict(results[req_id])
    out["status"] = "replay"
    out["scanned"] = counter.scanned
    return out


def plan(state, target, req_id, counter):
    """算一遍重置结果，不改状态。"""
    replay = _replay(state, req_id, counter)
    if replay is not None:
        return replay
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
    tokens_left = _tokens_left(state, counter)
    if tokens_left > 0:
        return {
            "req_id": req_id,
            "status": "ok",
            "reason": None,
            "fee": fee,
            "gold_after": state["gold"],
            "tokens_left": tokens_left - 1,
            "points": spent_points(target),
            "scanned": counter.scanned,
        }
    if state["gold"] - fee < 0:
        return {
            "req_id": req_id,
            "status": "no-funds",
            "reason": None,
            "fee": fee,
            "gold_after": state["gold"],
            "tokens_left": tokens_left,
            "points": spent_points(state["ranks"]),
            "scanned": counter.scanned,
        }
    return {
        "req_id": req_id,
        "status": "ok",
        "reason": None,
        "fee": fee,
        "gold_after": state["gold"] - fee,
        "tokens_left": tokens_left,
        "points": spent_points(target),
        "scanned": counter.scanned,
    }


def apply(state, target, req_id, counter):
    """结算一次重置并把结果落进台账。"""
    out = plan(state, target, req_id, counter)
    if out["status"] != "ok":
        return out
    used_token = False
    if state["tokens_total"] > 0:
        used = tokens_used(state, counter)
        used_token = used < state["tokens_total"]
        state["tokens_used"] = used + (1 if used_token else 0)
    state["ranks"] = dict(target)
    state["gold"] = out["gold_after"]
    state["ledger"].append({"req_id": req_id, "fee": out["fee"], "used_token": used_token})
    state.setdefault("results", {})[req_id] = dict(out)
    return out


def status(state):
    return {
        "points": spent_points(state["ranks"]),
        "gold": state["gold"],
        "tokens_left": _tokens_left(state, Counter()),
        "ledger": len(state["ledger"]),
    }
