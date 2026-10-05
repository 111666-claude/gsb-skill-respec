"""命令行入口。"""

import argparse
import json

from . import core


def _parse_sets(pairs):
    sets = {}
    for pair in pairs or []:
        tid, sep, value = pair.partition("=")
        if not sep:
            raise SystemExit("--set 需要 id=n 形式：" + pair)
        sets[tid.strip()] = int(value)
    return sets


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _save(path, state):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=1)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="respec")
    ap.add_argument("--sample", choices=["tier", "prereq", "token", "replay", "work"])
    sub = ap.add_subparsers(dest="cmd")
    for name in ("plan", "apply"):
        sp = sub.add_parser(name)
        sp.add_argument("--state", required=True)
        sp.add_argument("--req-id", required=True)
        sp.add_argument("--set", action="append", default=[])
    status_parser = sub.add_parser("status")
    status_parser.add_argument("--state", required=True)
    args = ap.parse_args(argv)

    if args.sample:
        from . import samples
        return samples.run(args.sample)
    if args.cmd is None:
        ap.print_help()
        return 2

    state = _load(args.state)
    if args.cmd == "status":
        print(json.dumps(core.status(state), ensure_ascii=False))
        return 0

    counter = core.Counter()
    target = core.build_target(_parse_sets(args.set))
    if args.cmd == "plan":
        out = core.plan(state, target, args.req_id, counter)
    else:
        out = core.apply(state, target, args.req_id, counter)
        _save(args.state, state)
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
