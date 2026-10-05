# skill-respec

天赋重置（洗点退点）的判定与台账。只用 Python 标准库。

```
python3 -m unittest discover -s tests
python3 -m respec plan  --state s.json --req-id r1 --set fireball=3 --set ice_nova=2
python3 -m respec apply --state s.json --req-id r1 --set fireball=3
python3 -m respec status --state s.json
python3 -m respec --sample=tier|prereq|token|replay|work
```

## 口径

- **花费**：每个天赋每级消耗 `cost` 点；要投入第 N 层（N≥2），第 1..N-1 层累计投入必须 ≥ `5×(N-1)`。
- **前置**：天赋声明的前置天赋点数必须 ≥ 1 才能投入。
- **洗点费**：每次重置按重置后投入的点数收费，每点 10 金币。
- **洗点券**：券总数大于已用券数时，本次重置用一张券抵扣全部金币，金币不变，券数减一。
- **幂等**：同一个 `req_id` 只结算一次；重复请求返回首次结果且不再改动状态。

## 不变量

- 任意天赋的等级不超过其 `max`，且不为负。
- 金币与剩余券数不会为负。
- `scanned` 不随台账长度放大：两千次结算的 `scanned` 不超过 9000。

## 输出契约

每次操作打印一行 JSON，键为 `req_id`、`status`（`ok` / `invalid` / `no-funds` / `replay`）、
`reason`（无效时的原因，其余为 null）、`fee`、`gold_after`、`tokens_left`、`points`、`scanned`。

`--sample=work` 只打印 `{"applies": N, "scanned": N}`。
