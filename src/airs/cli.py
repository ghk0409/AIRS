from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import sys

from .config import load_config
from .doctor import diagnose
from .history import RunHistory
from .models import ALLOWED_ROLES, ContractError, ModelTier, Provider, RouteDecision, TaskContract, max_tier
from .routing import HybridRouter, RouteOverrides
from .review_scope import file_hashes, selected_files
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
        if name == "review":
            command.add_argument("--run-id", help="review a previous AIRS run without rerouting")
            command.add_argument("--file", action="append", dest="files", help="limit review to this file (repeatable)")
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
    status.add_argument("--run-id", help="show one run instead of the latest")
    doctor = subparsers.add_parser("doctor")
    doctor.add_argument("--root", default=".", help="project root for configuration checks")
    doctor.add_argument("--offline", action="store_true", help="skip CLI login and model catalog probes")
    history = subparsers.add_parser("history")
    history.add_argument("--root", default=".", help="project root containing run history")
    history_actions = history.add_subparsers(dest="history_action", required=True)
    prune = history_actions.add_parser("prune")
    prune.add_argument("--older-than", type=int, default=None, help="days; defaults to configured retention")
    prune.add_argument("--apply", action="store_true", help="delete matching records; otherwise preview")
    scrub = history_actions.add_parser("scrub")
    scrub.add_argument("run_id", help="run to remove task text and agent output from")
    scrub.add_argument("--apply", action="store_true", help="redact the record; otherwise preview")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_config(args.config)
        if args.command == "doctor":
            result = diagnose(config, Path(args.root).resolve(), offline=args.offline)
            _print(result, args.json)
            return 0 if result["ok"] else 1
        if args.command == "history":
            history = RunHistory(Path(args.root).resolve(), str(config["history_dir"]))
            if args.history_action == "prune":
                days = args.older_than or int(config.get("history_retention_days", 30))
                candidates = history.prune(days, apply=args.apply)
                result = {"action": "prune", "applied": args.apply, "run_ids": candidates}
            else:
                history.scrub(args.run_id, apply=args.apply)
                result = {"action": "scrub", "applied": args.apply, "run_ids": [args.run_id]}
            _print(result, args.json)
            return 0
        if args.command == "status":
            history = RunHistory(Path(args.root).resolve(), str(config["history_dir"]))
            latest = history.load(args.run_id) if args.run_id else history.latest()
            if latest is None:
                print("No AIRS run history found.")
                return 1
            _print(latest, args.json)
            return 0
        source_run_id = args.run_id if args.command == "review" else None
        source_files = None
        if source_run_id:
            if args.task or args.prompt is not None:
                raise ContractError("--run-id cannot be combined with a task file or --prompt")
            history_root = Path(args.root or Path.cwd()).resolve()
            source = RunHistory(history_root, str(config["history_dir"])).load(source_run_id)
            if source.get("kind") != "run":
                raise ContractError("--run-id must identify an AIRS run")
            task = TaskContract.from_mapping(source["task"])
            if task.project_root != history_root:
                raise ContractError("run belongs to a different project root")
            primary_steps = [step for step in source.get("steps", []) if step.get("name") == "primary"]
            if not primary_steps or not primary_steps[0].get("ok", primary_steps[0].get("returncode") == 0):
                raise ContractError("cannot review a run whose primary agent failed")
            route = source["decision"]
            decision = RouteDecision(
                provider=Provider(route["provider"]), tier=ModelTier(route["tier"]),
                review=bool(route.get("review")),
                reviewer=Provider(route["reviewer"]) if route.get("reviewer") else None,
                role="reviewer", source="prior-run", rationale=[f"review run {source_run_id}"],
            )
            source_files = source.get("review_files")
            if source_files:
                source_files = selected_files(task.project_root, source_files)
            if source_files and source.get("review_file_hashes") and args.files is None:
                try:
                    current_hashes = file_hashes(task.project_root, source_files)
                except OSError as exc:
                    raise ContractError(f"review files changed or disappeared since the run: {exc}") from exc
                if current_hashes != source["review_file_hashes"]:
                    raise ContractError("review files changed since the run; use --file for a new review scope")
        elif args.command in {"plan", "run", "review"} and args.prompt is not None:
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
        if source_run_id and overrides.tier:
            decision.tier = max_tier(decision.tier, overrides.tier)
        if not source_run_id:
            decision = HybridRouter(config).plan(task, overrides)
        if args.command == "plan":
            _print(decision.to_dict(), args.json)
            return 0
        workflow = Workflow(config)
        progress = _progress if sys.stderr.isatty() and not args.json else None
        record = (
            workflow.run(task, decision, args.dry_run, progress=progress)
            if args.command == "run"
            else workflow.review(
                task, decision, overrides.provider, args.dry_run, progress=progress,
                files=args.files if args.files is not None else source_files,
                source_run_id=source_run_id,
            )
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
    if "checks" in data:
        for check in data["checks"]:
            print(f"{'ok' if check['ok'] else 'fail'}: {check['name']} — {check['detail']}")
        return
    if "action" in data:
        print(f"{data['action']}: {'applied' if data['applied'] else 'preview'}")
        for run_id in data["run_ids"]:
            print(run_id)
        return
    if "run_id" in data:
        print(f"run: {data['run_id']}")
        print(f"status: {data['status']}")
        if data.get("review_error"):
            print(f"review_error: {data['review_error']}", file=sys.stderr)
        for step in data.get("steps", []):
            suffix = " (dry run)" if step.get("dry_run") else ""
            print(f"{step['name']}: returncode={step['returncode']}{suffix}")
            output = step.get("response") if step.get("provider") == "antigravity" else step.get("stdout")
            if output:
                print(output.rstrip())
            if not step.get("ok", step["returncode"] == 0) and step.get("error"):
                print(step["error"], file=sys.stderr)
            if not step.get("ok", step["returncode"] == 0) and step.get("stderr"):
                print(step["stderr"].rstrip(), file=sys.stderr)
        return
    print(f"provider: {data['provider']}")
    print(f"tier: {data['tier']} ({data.get('model')}, effort={data.get('effort')})")
    print(f"review: {str(data['review']).lower()}")
    print(f"source: {data['source']}")
    for reason in data.get("rationale", []):
        print(f"- {reason}")


def _progress(stage: str, elapsed: float, metrics: dict[str, int] | None = None) -> None:
    if elapsed == 0:
        print(f"{stage}: started", file=sys.stderr, flush=True)
    else:
        detail = f", {metrics['file_reads']} files, {metrics['input_tokens']} input tokens" if metrics else ""
        print(f"{stage}: still running ({elapsed:.0f}s{detail})", file=sys.stderr, flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
