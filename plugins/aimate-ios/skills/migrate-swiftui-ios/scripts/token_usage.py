#!/usr/bin/env python3
"""Sum the tokens a Claude Code session used between two moments.

Reads the session transcript that Claude Code writes under ~/.claude/projects
(the main conversation plus its subagents) and totals the `usage` of every model
response, per model. Prints nothing but numbers and model names.

Usage:
  token_usage.py now                         print the current UTC time, to mark a start
  token_usage.py sum [--session ID] [--since ISO] [--until ISO] [--json]

--session defaults to $CLAUDE_CODE_SESSION_ID. Exits with status 2 when the
transcript cannot be found, for example on another host than Claude Code.
"""
import argparse
import datetime as dt
import glob
import json
import os
import sys

FIELDS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")


def now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def parse_time(value):
    if not value:
        return None
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def transcripts(session):
    root = os.path.expanduser("~/.claude/projects")
    main = glob.glob(os.path.join(root, "*", f"{session}.jsonl"))
    subs = glob.glob(os.path.join(root, "*", session, "subagents", "*.jsonl"))
    return main, subs


def collect(files, since, until):
    # A response is written as several lines that repeat its usage; keep the
    # largest value per field for each (message id, request id).
    responses = {}
    for path in files:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                message = entry.get("message")
                if not isinstance(message, dict) or not isinstance(message.get("usage"), dict):
                    continue
                stamp = parse_time(entry.get("timestamp"))
                if stamp is None or (since and stamp < since) or (until and stamp > until):
                    continue
                key = (path, message.get("id"), entry.get("requestId"))
                usage = message["usage"]
                current = responses.setdefault(key, {"model": message.get("model", "unknown"), **{f: 0 for f in FIELDS}})
                for field in FIELDS:
                    value = usage.get(field)
                    if isinstance(value, int) and value > current[field]:
                        current[field] = value
    totals = {}
    for response in responses.values():
        model = totals.setdefault(response["model"], {"responses": 0, **{f: 0 for f in FIELDS}})
        model["responses"] += 1
        for field in FIELDS:
            model[field] += response[field]
    return totals


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("now")
    summed = sub.add_parser("sum")
    summed.add_argument("--session", default=os.environ.get("CLAUDE_CODE_SESSION_ID"))
    summed.add_argument("--since")
    summed.add_argument("--until")
    summed.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.command == "now":
        print(now())
        return 0
    if not args.session:
        print("No session id: pass --session or run inside Claude Code.", file=sys.stderr)
        return 2
    main_files, sub_files = transcripts(args.session)
    if not main_files:
        print(f"No transcript found for session {args.session}.", file=sys.stderr)
        return 2
    since, until = parse_time(args.since), parse_time(args.until)
    result = {
        "session": args.session,
        "since": args.since,
        "until": args.until or now(),
        "main": collect(main_files, since, until),
        "subagents": collect(sub_files, since, until),
    }
    grand = {f: 0 for f in FIELDS}
    for part in ("main", "subagents"):
        for model in result[part].values():
            for field in FIELDS:
                grand[field] += model[field]
    grand["total"] = sum(grand[f] for f in FIELDS)
    result["total"] = grand

    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    print(f"Session {args.session}, {args.since or 'start'} to {result['until']}")
    print(f"{'part':<10} {'model':<28} {'input':>12} {'cache write':>12} {'cache read':>14} {'output':>10}")
    for part in ("main", "subagents"):
        for name, model in sorted(result[part].items()):
            print(f"{part:<10} {name:<28} {model['input_tokens']:>12,} {model['cache_creation_input_tokens']:>12,} "
                  f"{model['cache_read_input_tokens']:>14,} {model['output_tokens']:>10,}")
    print(f"{'total':<39} {grand['input_tokens']:>12,} {grand['cache_creation_input_tokens']:>12,} "
          f"{grand['cache_read_input_tokens']:>14,} {grand['output_tokens']:>10,}")
    print(f"All tokens: {grand['total']:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
