from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import sys

from .config import load_config
from .history import RunHistory
from .models import ContractError, ModelTier, Provider, TaskContract
from .routing import HybridRouter, RouteOverrides
from .workflow import Workflow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="airs", description="AIRS local agent orchestrator")
    parser.add_argument("--config", help="configuration YAML (default: AIRS_CONFIG or ./airs.yaml)")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "run", "review"):
        command = subparsers.add_parser(name)
        command.add_argument("task", help="task contract YAML or JSON")
        command.add_argument("--provider", choices=[item.value for item in Provider])
        command.add_argument("--tier", choices=[item.value for item in ModelTier])
        command.add_argument("--no-review", action="store_true")
        if name in {"run", "review"}:
            command.add_argument("--dry-run", action="store_true")
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
        task = TaskContract.load(args.task)
        if not task.project_root.is_dir():
            raise ContractError(f"project_root is not a directory: {task.project_root}")
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
        record = (
            workflow.run(task, decision, args.dry_run)
            if args.command == "run"
            else workflow.review(task, decision, overrides.provider, args.dry_run)
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
            print(f"{step['name']}: returncode={step['returncode']}")
        return
    print(f"provider: {data['provider']}")
    print(f"tier: {data['tier']} ({data.get('model')}, effort={data.get('effort')})")
    print(f"review: {str(data['review']).lower()}")
    print(f"source: {data['source']}")
    for reason in data.get("rationale", []):
        print(f"- {reason}")


if __name__ == "__main__":
    raise SystemExit(main())
