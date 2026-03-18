"""Tests for the DAG engine."""

from pathlib import Path

import pytest

from crm_core.dag.engine import DAGEngine, RunResult
from crm_core.dag.nodes import make_node


# ── workflow fixtures ─────────────────────────────────────────────────────────

SIMPLE_WORKFLOW = {
    "id": "simple_test",
    "description": "A simple two-node workflow for testing",
    "nodes": [
        {"id": "step_a", "type": "notify", "params": {"message": "Hello {{ name }}", "channel": "log"}},
        {"id": "step_b", "type": "action", "params": {"action": "log_run"}},
    ],
    "edges": [["step_a", "step_b"]],
}

CONDITION_WORKFLOW = {
    "id": "condition_test",
    "nodes": [
        {
            "id": "check",
            "type": "condition",
            "params": {
                "expression": "score > 50",
                "true_branch": "high_value",
                "false_branch": "low_value",
            },
        },
        {"id": "high_value", "type": "notify", "params": {"message": "High value!", "channel": "log"}},
        {"id": "low_value", "type": "notify", "params": {"message": "Low value.", "channel": "log"}},
        {"id": "done", "type": "action", "params": {"action": "log_run"}},
    ],
    "edges": [
        ["check", "high_value"],
        ["check", "low_value"],
        ["high_value", "done"],
        ["low_value", "done"],
    ],
}

CYCLIC_WORKFLOW = {
    "id": "cyclic_bad",
    "nodes": [
        {"id": "a", "type": "action", "params": {}},
        {"id": "b", "type": "action", "params": {}},
    ],
    "edges": [["a", "b"], ["b", "a"]],
}


# ── tests ─────────────────────────────────────────────────────────────────────

def test_load_simple_workflow() -> None:
    engine = DAGEngine()
    wf = engine.load_workflow(SIMPLE_WORKFLOW)
    assert wf.id == "simple_test"
    assert set(wf.node_ids) == {"step_a", "step_b"}


def test_topological_order() -> None:
    engine = DAGEngine()
    wf = engine.load_workflow(SIMPLE_WORKFLOW)
    order = wf.topological_order()
    assert order.index("step_a") < order.index("step_b")


def test_cyclic_workflow_raises() -> None:
    engine = DAGEngine()
    with pytest.raises(ValueError, match="cycle"):
        engine.load_workflow(CYCLIC_WORKFLOW)


def test_run_simple_workflow() -> None:
    engine = DAGEngine()
    engine.load_workflow(SIMPLE_WORKFLOW)
    result = engine.run("simple_test", {"name": "Alice"})
    assert result.status == "completed"
    assert len(result.steps) == 2
    assert all(s.status == "ok" for s in result.steps)


def test_run_condition_true_branch() -> None:
    engine = DAGEngine()
    engine.load_workflow(CONDITION_WORKFLOW)
    result = engine.run("condition_test", {"score": 80})
    assert result.status == "completed"
    step_map = {s.node_id: s for s in result.steps}
    assert step_map["high_value"].status == "ok"
    assert step_map["low_value"].status == "skipped"


def test_run_condition_false_branch() -> None:
    engine = DAGEngine()
    engine.load_workflow(CONDITION_WORKFLOW)
    result = engine.run("condition_test", {"score": 20})
    step_map = {s.node_id: s for s in result.steps}
    assert step_map["low_value"].status == "ok"
    assert step_map["high_value"].status == "skipped"


def test_run_unknown_workflow_raises() -> None:
    engine = DAGEngine()
    with pytest.raises(KeyError):
        engine.run("not_loaded", {})


def test_run_result_markdown(tmp_path: Path) -> None:
    engine = DAGEngine(vault_root=tmp_path)
    engine.load_workflow(SIMPLE_WORKFLOW)
    result = engine.run("simple_test", {"name": "Test"})
    run_note = tmp_path / "workflows" / "runs" / "simple_test" / f"{result.run_id}.md"
    assert run_note.exists()
    content = run_note.read_text()
    assert "simple_test" in content
    assert result.run_id in content


def test_template_rendering_in_notify() -> None:
    engine = DAGEngine()
    engine.load_workflow(SIMPLE_WORKFLOW)
    result = engine.run("simple_test", {"name": "World"})
    notify_step = next(s for s in result.steps if s.node_id == "step_a")
    assert notify_step.output.get("message") == "Hello World"


def test_make_node_unknown_type_raises() -> None:
    with pytest.raises(ValueError, match="Unknown node type"):
        make_node({"id": "x", "type": "magic_unknown", "params": {}})


def test_load_from_file(tmp_path: Path) -> None:
    import yaml

    wf_file = tmp_path / "test_wf.yaml"
    wf_file.write_text(yaml.dump(SIMPLE_WORKFLOW))

    engine = DAGEngine()
    wf = engine.load_from_file(wf_file)
    assert wf.id == "simple_test"
