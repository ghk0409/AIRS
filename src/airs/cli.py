from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import sys

from .config import load_config
from .history import RunHistory
from .models import ALLOWED_ROLES, ContractError, ModelTier, Provider, TaskContract
from .routing import HybridRouter, RouteOverrides
from .workflow import Workflow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="airs", description="AIRS local agent orchestrator")
    parser.add_argument("--config", help="configuration YAML (default: AIRS_CONFIG or ./airs.yaml)")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "run", "review"):
        command = subparsers.add_parser(name)
        command.add_argument("task", nargs="?", help="task contract YAML or JSON")
        command.add_argument("-p", "--prompt", help="request text; uses the current directory")
        command.add_argument("--root", help="project root for --prompt (default: current directory)")
        command.add_argument("--role", choices=sorted(ALLOWED_ROLES), default="implementer")
        command.add_argument("--provider", choices=[item.value for item in Provider])
        command.add_argument("--tier", choices=[item.value for item in ModelTier])
        command.add_argument("--no-review", action="store_true")
        if name in {"run", "review"}:
            command.add_argument("--dry-run", action="store_true")
        if name == "run":
            command.add_argument(
                "--verify-cmd", action="append", default=[],
                help="run this command after the agent and review (repeatable)",
            )
    verify = subparsers.add_parser("verify")
    verify.add_argument("task", help="task contract YAML or JSON")
    verify.add_argument("--dry-run", action="store_true")
    status = subparsers.add_parser("status")
    status.add_argument("--root", default=".", help="project root containing run history")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_config(args.config)
        if args.command == "status":
            latest = RunHistory(Path(args.root).resolve(), str(config["history_dir"])).latest()
            if latest is None:
                print("No AIRS run history found.")
                return 1
            _print(latest, args.json)
            return 0
        if args.command in {"plan", "run", "review"} and args.prompt is not None:
            if args.task:
                raise ContractError("provide either a task file or --prompt, not both")
            task = TaskContract.from_prompt(args.prompt, args.root or Path.cwd(), args.role)
        else:
            if not args.task:
                raise ContractError("provide a task contract or use --prompt")
            if args.command in {"plan", "run", "review"} and args.root:
                raise ContractError("--root applies only to --prompt")
            task = TaskContract.load(args.task)
        if not task.project_root.is_dir():
            raise ContractError(f"project_root is not a directory: {task.project_root}")
        if args.command == "run" and args.verify_cmd:
            task.verification.commands.extend(args.verify_cmd)
        if args.command == "verify":
            record = Workflow(config).verify(task, args.dry_run)
            _print(record, args.json)
            return 0 if record["status"] == "completed" else 1
        overrides = RouteOverrides(
            provider=Provider(args.provider) if args.provider else None,
            tier=ModelTier(args.tier) if args.tier else None,
            no_review=args.no_review,
        )
        decision = HybridRouter(config).plan(task, overrides)
        if args.command == "plan":
            _print(decision.to_dict(), args.json)
            return 0
        workflow = Workflow(config)
        progress = _progress if sys.stderr.isatty() and not args.json else None
        record = (
            workflow.run(task, decision, args.dry_run, progress=progress)
            if args.command == "run"
            else workflow.review(task, decision, overrides.provider, args.dry_run, progress=progress)
        )
        _print(record, args.json)
        return 0 if record["status"] == "completed" else 1
    except (ContractError, ValueError, RuntimeError, OSError) as exc:
        print(f"airs: {exc}", file=sys.stderr)
        return 2


def _print(data: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return
    if "run_id" in data:
        print(f"run: {data['run_id']}")
        print(f"status: {data['status']}")
        for step in data.get("steps", []):
            suffix = " (dry run)" if step.get("dry_run") else ""
            print(f"{step['name']}: returncode={step['returncode']}{suffix}")
            if step.get("stdout"):
                print(step["stdout"].rstrip())
            if step["returncode"] != 0 and step.get("stderr"):
                print(step["stderr"].rstrip(), file=sys.stderr)
        return
    print(f"provider: {data['provider']}")
    print(f"tier: {data['tier']} ({data.get('model')}, effort={data.get('effort')})")
    print(f"review: {str(data['review']).lower()}")
    print(f"source: {data['source']}")
    for reason in data.get("rationale", []):
        print(f"- {reason}")


def _progress(stage: str, elapsed: float) -> None:
    if elapsed == 0:
        print(f"{stage}: started", file=sys.stderr, flush=True)
    else:
        print(f"{stage}: still running ({elapsed:.0f}s)", file=sys.stderr, flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
