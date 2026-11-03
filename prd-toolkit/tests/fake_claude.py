#!/usr/bin/env python3
"""A stand-in for `claude -p` (and for a pack grader) in the prd_judge tests. Standard library only.

Each call appends one JSON line to $FAKE_CLAUDE_LOG: {"argv", "stdin", "cwd", "cwd_files"}, plus "rubric_file" (the
text of the file after `--rubric`) when called as a pack grader.
If $FAKE_CLAUDE_EXIT is a non-zero code, it writes $FAKE_CLAUDE_STDERR to stderr and exits with that code.
Otherwise it prints the reply in $FAKE_CLAUDE_REPLY: the value itself, or the contents of the file it names. A reply
that is a JSON array is a script of replies, one per call (the n-th call, counted from the log, prints element n; the
last element repeats); an element that is a string is printed as is, any other element as JSON.
"""
import json
import os
import sys


def main() -> int:
    stdin = "" if sys.stdin is None or sys.stdin.isatty() else sys.stdin.read()
    log = os.environ.get("FAKE_CLAUDE_LOG")
    calls = 0
    if log:
        try:
            with open(log, encoding="utf-8") as f:
                calls = sum(1 for line in f if line.strip())
        except OSError:
            calls = 0
        cwd = os.getcwd()
        entry = {"argv": sys.argv[1:], "stdin": stdin, "cwd": cwd, "cwd_files": sorted(os.listdir(cwd))}
        if "--rubric" in sys.argv[1:-1]:
            with open(sys.argv[sys.argv.index("--rubric") + 1], encoding="utf-8") as f:
                entry["rubric_file"] = f.read()
        with open(log, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    code = int(os.environ.get("FAKE_CLAUDE_EXIT") or "0")
    if code:
        sys.stderr.write(os.environ.get("FAKE_CLAUDE_STDERR", ""))
        return code
    reply = os.environ.get("FAKE_CLAUDE_REPLY", "")
    if reply and os.path.isfile(reply):
        with open(reply, encoding="utf-8") as f:
            reply = f.read()
    try:
        script = json.loads(reply)
    except ValueError:
        script = None
    if isinstance(script, list) and script:
        item = script[min(calls, len(script) - 1)]
        reply = item if isinstance(item, str) else json.dumps(item)
    sys.stdout.write(reply)
    return 0


if __name__ == "__main__":
    sys.exit(main())
