#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0", "sqlglot>=25", "openapi-spec-validator>=0.7"]
# ///
"""Plan and run a PRD's deploy runbook. Exit 0 done, 1 refused, 2 usage or tool error, 3 human step, 4 failed."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from prdlint import deps  # noqa: E402

for _module, _package in (("yaml", "pyyaml"), ("sqlglot", "sqlglot"), ("openapi_spec_validator", "openapi-spec-validator")):
    deps.require(_module, _package)

from prdlint import deploy, model  # noqa: E402


def _fail(message: str) -> int:
    print(f"prd_deploy: {message}", file=sys.stderr)
    return deploy.EXIT["usage"]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="prd_deploy.py", description="Plan and run a PRD's deploy runbook.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, text in (("plan", "print the steps a run would take; runs nothing"), ("run", "pre-flight, then run the steps in order")):
        p = sub.add_parser(name, help=text)
        p.add_argument("prd_dir")
        p.add_argument("--until", metavar="ENV", help="stop after the last step on this environment")
        if name == "run":
            p.add_argument("--timeout", type=int, default=deploy.DEFAULT_TIMEOUT, metavar="SECONDS", help="per command (default 600)")
    return parser


def _steps_or_message(prd: model.Prd, until: str | None):
    """The planned steps, or an error string when the runbook cannot be run."""
    try:
        steps = deploy.plan_steps(prd, until)
    except ValueError as e:
        return None, str(e)
    if not steps:
        return None, "the PRD has no runbook steps"
    for s in steps:
        if s.actor not in ("agent", "human") or (s.actor == "agent" and s.run is None and s.tests is None):
            return None, f"step {s.number} does not match the runbook grammar; run prd_lint"
    return steps, None


def main(argv: list[str]) -> int:
    try:
        args = _parser().parse_args(argv)
    except SystemExit as e:
        return 0 if e.code in (0, None) else deploy.EXIT["usage"]
    if args.command == "run" and args.timeout < 1:
        return _fail("--timeout must be at least 1")
    try:
        prd = model.load(Path(args.prd_dir))
    except model.NotAPrd as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"internal error: {type(e).__name__}: {e}")
    if prd.adoption_unmigrated:
        return _fail(f"{prd.root.as_posix()}/prd.md: {model.UNMIGRATED}")
    steps, problem = _steps_or_message(prd, args.until)
    if problem:
        return _fail(problem)
    try:
        if args.command == "plan":
            for s in steps:
                print(f"{s.number} {s.actor} {s.env}: {s.title}" + (f" — {deploy.step_command(s)}" if s.actor == "agent" else ""))
            return 0
        repo_root = model.repo_root(prd.root)
        reasons = deploy.preflight(prd, repo_root)
        if reasons:
            for r in reasons:
                print(f"refused: {r}")
            print("prd-deploy: refused step=0 run=none")
            return deploy.EXIT["refused"]
        run_id = deploy.new_run_id(repo_root, args.until)
        try:
            deploy.start_run(prd, repo_root, run_id, args.until)
        except Exception:
            (deploy.log_dir(repo_root) / f"{run_id}.jsonl").unlink(missing_ok=True)
            raise
        print(f"run: {run_id}", flush=True)
        try:
            state, number = deploy.run_steps(prd, repo_root, run_id, steps, 1, args.timeout)
        except Exception as e:  # the run has started: say so and fail it
            print(f"prd_deploy: internal error: {type(e).__name__}: {e}", file=sys.stderr)
            state, number = "failed", 0
        print(f"prd-deploy: {state} step={number} run={run_id}")
        return deploy.EXIT[state]
    except Exception as e:
        return _fail(f"internal error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        _stream.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
