"""DAG workflow engine.

Responsibilities
----------------
1. Load a workflow YAML definition.
2. Build a ``networkx.DiGraph``.
3. Validate: no cycles, all referenced nodes exist.
4. Execute nodes in topological order, honouring condition branches.
5. Log execution steps (structured JSON to stderr / vault note).

Design principles
-----------------
- No LLM involved – all routing is deterministic.
- Condition nodes use a sandboxed ``eval`` (no ``__builtins__``).
- Execution is synchronous and single-process.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import networkx as nx
import yaml

from crm_core.dag.nodes import ConditionNode, DelayNode, NodeType, NotifyNode, make_node

log = logging.getLogger(__name__)


# ── Execution result ──────────────────────────────────────────────────────────

@dataclass
class StepResult:
    node_id: str
    node_type: str
    status: str  # ok | skipped | error
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    duration_ms: float = 0.0


@dataclass
class RunResult:
    workflow_id: str
    run_id: str
    status: str  # completed | failed
    steps: list[StepResult] = field(default_factory=list)
    error: str | None = None

    def to_markdown(self) -> str:
        """Format execution log as a vault markdown note."""
        lines = [
            "---",
            f"workflow_id: {self.workflow_id}",
            f"run_id: {self.run_id}",
            f"status: {self.status}",
            f"steps: {len(self.steps)}",
            "---",
            "",
            f"# Workflow Run: {self.workflow_id}",
            "",
            f"**Run ID**: `{self.run_id}`  **Status**: `{self.status}`",
            "",
            "## Steps",
            "",
        ]
        for s in self.steps:
            icon = "✅" if s.status == "ok" else ("⏭️" if s.status == "skipped" else "❌")
            lines.append(f"- {icon} `{s.node_id}` ({s.node_type}) – {s.status} [{s.duration_ms:.0f} ms]")
            if s.error:
                lines.append(f"  - **Error**: {s.error}")
        return "\n".join(lines)


# ── Workflow definition ────────────────────────────────────────────────────────

class Workflow:
    """A validated, executable workflow loaded from YAML."""

    def __init__(self, definition: dict[str, Any]) -> None:
        self.id: str = definition["id"]
        self.description: str = definition.get("description", "")
        self.version: str = str(definition.get("version", "1.0"))

        # Build node registry
        self._nodes: dict[str, NodeType] = {
            n.id: n for n in (make_node(nd) for nd in definition.get("nodes", []))
        }

        # Build DiGraph
        self._graph = nx.DiGraph()
        self._graph.add_nodes_from(self._nodes.keys())
        for edge in definition.get("edges", []):
            src, dst = edge[0], edge[1]
            self._validate_node_ref(src)
            self._validate_node_ref(dst)
            self._graph.add_edge(src, dst)

        self._validate()

    def _validate_node_ref(self, node_id: str) -> None:
        if node_id not in self._nodes:
            raise ValueError(f"Workflow {self.id!r}: edge references unknown node {node_id!r}")

    def _validate(self) -> None:
        if not nx.is_directed_acyclic_graph(self._graph):
            cycle = nx.find_cycle(self._graph)
            raise ValueError(f"Workflow {self.id!r} has a cycle: {cycle}")

    @property
    def node_ids(self) -> list[str]:
        return list(self._nodes.keys())

    def topological_order(self) -> list[str]:
        return list(nx.topological_sort(self._graph))


# ── Engine ────────────────────────────────────────────────────────────────────

def _safe_eval(expression: str, context: dict[str, Any]) -> bool:
    """Evaluate a boolean expression in a sandboxed namespace.

    Only the context dict keys are available; no builtins.
    """
    try:
        result = eval(expression, {"__builtins__": {}}, context)  # noqa: S307
        return bool(result)
    except Exception as exc:
        raise ValueError(f"Condition expression error: {exc}") from exc


def _render_template(text: str, context: dict[str, Any]) -> str:
    """Very simple {{ key }} template substitution (no LLM)."""
    import re

    def replace(m: re.Match) -> str:
        key = m.group(1).strip()
        # Support nested key access: deal.title → context['deal']['title']
        parts = key.split(".")
        val: Any = context
        for p in parts:
            if isinstance(val, dict):
                val = val.get(p, f"{{{{{key}}}}}")
            else:
                val = f"{{{{{key}}}}}"
                break
        return str(val)

    return re.sub(r"\{\{(.+?)\}\}", replace, text)


class DAGEngine:
    """Execute CRM workflows defined as networkx DAGs."""

    def __init__(self, vault_root: Path | None = None) -> None:
        self._vault_root = vault_root
        self._workflows: dict[str, Workflow] = {}

    def load_workflow(self, definition: dict[str, Any]) -> Workflow:
        """Parse, validate, and register a workflow definition dict."""
        wf = Workflow(definition)
        self._workflows[wf.id] = wf
        log.info("Loaded workflow %r (v%s)", wf.id, wf.version)
        return wf

    def load_from_file(self, path: Path) -> Workflow:
        """Load a workflow from a YAML file."""
        with open(path, encoding="utf-8") as fh:
            definition = yaml.safe_load(fh)
        return self.load_workflow(definition)

    def load_from_directory(self, directory: Path) -> list[Workflow]:
        """Load all *.yaml workflow files from a directory."""
        workflows = []
        for yaml_file in sorted(directory.glob("*.yaml")):
            try:
                workflows.append(self.load_from_file(yaml_file))
            except Exception as exc:
                log.error("Failed to load workflow %s: %s", yaml_file.name, exc)
        return workflows

    def run(self, workflow_id: str, context: dict[str, Any]) -> RunResult:
        """Execute a registered workflow with the given context dict.

        Nodes are executed in topological order.  Condition nodes determine
        which downstream branch is active; the inactive branch is skipped.
        """
        if workflow_id not in self._workflows:
            raise KeyError(f"Workflow {workflow_id!r} is not loaded.")

        wf = self._workflows[workflow_id]
        run_id = str(uuid.uuid4())[:8]
        result = RunResult(workflow_id=workflow_id, run_id=run_id, status="completed")
        skipped: set[str] = set()

        log.info("Starting workflow %r run_id=%s", workflow_id, run_id)

        for node_id in wf.topological_order():
            node = wf._nodes[node_id]  # noqa: SLF001
            if node_id in skipped:
                result.steps.append(StepResult(node_id=node_id, node_type=node.type, status="skipped"))
                log.debug("Skipped node %s", node_id)
                continue

            step = self._execute_node(node, context, run_id, wf)
            result.steps.append(step)

            if step.status == "error":
                result.status = "failed"
                result.error = step.error
                log.error("Workflow %r failed at node %s: %s", workflow_id, node_id, step.error)
                break

            # Handle condition branching: skip the inactive branch
            if isinstance(node, ConditionNode):
                branch_taken = step.output.get("branch_taken")
                inactive = (
                    node.false_branch if branch_taken == "true" else node.true_branch
                )
                if inactive:
                    skipped.add(inactive)

        self._persist_run(result, context)
        log.info("Workflow %r run_id=%s status=%s", workflow_id, run_id, result.status)
        return result

    def _execute_node(
        self,
        node: NodeType,
        context: dict[str, Any],
        run_id: str,
        wf: Workflow,
    ) -> StepResult:
        t0 = time.monotonic()
        try:
            output = self._dispatch(node, context)
            duration = (time.monotonic() - t0) * 1000
            log.debug(
                json.dumps({"node": node.id, "type": node.type, "status": "ok", "ms": round(duration, 1)})
            )
            return StepResult(
                node_id=node.id,
                node_type=node.type,
                status="ok",
                output=output,
                duration_ms=duration,
            )
        except Exception as exc:
            duration = (time.monotonic() - t0) * 1000
            return StepResult(
                node_id=node.id,
                node_type=node.type,
                status="error",
                error=str(exc),
                duration_ms=duration,
            )

    def _dispatch(self, node: NodeType, context: dict[str, Any]) -> dict[str, Any]:
        """Route execution to the correct handler based on node type."""
        if isinstance(node, ConditionNode):
            result = _safe_eval(node.expression, context)
            branch = "true" if result else "false"
            log.debug("Condition %s → %s", node.id, branch)
            return {"branch_taken": branch, "result": result}

        if isinstance(node, NotifyNode):
            msg = _render_template(node.message, context)
            log.info("[NOTIFY][%s] %s", node.channel, msg)
            return {"message": msg, "channel": node.channel}

        if isinstance(node, DelayNode):
            time.sleep(node.seconds)
            return {"slept_seconds": node.seconds}

        # ActionNode – dispatch by params.action
        action = node.params.get("action", "unknown")
        params = {k: _render_template(str(v), context) if isinstance(v, str) else v
                  for k, v in node.params.items() if k != "action"}

        log.info("[ACTION] %s params=%s", action, params)

        if action == "log_run":
            return {"logged": True}

        if action in ("create_task", "update_contact", "log_run"):
            # These would call VaultService in a full implementation.
            # Returning the rendered params is sufficient for testing.
            return {"action": action, "params": params}

        return {"action": action, "params": params}

    def _persist_run(self, result: RunResult, context: dict[str, Any]) -> None:
        """Write the execution log to the vault (if vault_root is set)."""
        if self._vault_root is None:
            return
        run_dir = self._vault_root / "workflows" / "runs" / result.workflow_id
        run_dir.mkdir(parents=True, exist_ok=True)
        run_path = run_dir / f"{result.run_id}.md"
        run_path.write_text(result.to_markdown(), encoding="utf-8")
        log.debug("Run log written to %s", run_path)
