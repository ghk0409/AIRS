from pathlib import Path

import pytest

from airs.models import ContractError, TaskContract


def test_contract_resolves_relative_project_root(tmp_path: Path) -> None:
    contract = tmp_path / "task.yaml"
    contract.write_text("id: t1\ntitle: Test\nobjective: Do the work\nproject_root: .\n", encoding="utf-8")
    task = TaskContract.load(contract)
    assert task.project_root == tmp_path.resolve()


def test_contract_rejects_missing_fields() -> None:
    with pytest.raises(ContractError, match="objective"):
        TaskContract.from_mapping({"id": "t1", "title": "Test", "project_root": "."})


def test_contract_rejects_unknown_fields_and_roles() -> None:
    base = {"id": "t1", "title": "Test", "objective": "Work", "project_root": "."}
    with pytest.raises(ContractError, match="unknown field"):
        TaskContract.from_mapping({**base, "surprise": True})
    with pytest.raises(ContractError, match="unsupported role"):
        TaskContract.from_mapping({**base, "role": "admin"})
