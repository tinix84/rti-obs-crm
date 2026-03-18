"""Workflow node type definitions.

Each node type is a dataclass with a `type` discriminator field.
Node execution logic is kept in `engine.py`; nodes are pure data containers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class ActionNode:
    """Execute a named CRM action (create_task, update_contact, log_run…)."""

    id: str
    type: Literal["action"] = "action"
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConditionNode:
    """Evaluate a boolean Python expression against the workflow context.

    The expression is evaluated in a sandboxed namespace (no builtins).
    ``true_branch`` and ``false_branch`` reference downstream node IDs.
    """

    id: str
    type: Literal["condition"] = "condition"
    params: dict[str, Any] = field(default_factory=dict)

    @property
    def expression(self) -> str:
        return str(self.params.get("expression", "False"))

    @property
    def true_branch(self) -> str | None:
        return self.params.get("true_branch")

    @property
    def false_branch(self) -> str | None:
        return self.params.get("false_branch")


@dataclass
class NotifyNode:
    """Emit a notification message (to log, webhook, etc.)."""

    id: str
    type: Literal["notify"] = "notify"
    params: dict[str, Any] = field(default_factory=dict)

    @property
    def message(self) -> str:
        return str(self.params.get("message", ""))

    @property
    def channel(self) -> str:
        return str(self.params.get("channel", "log"))


@dataclass
class DelayNode:
    """Pause execution for a given number of seconds."""

    id: str
    type: Literal["delay"] = "delay"
    params: dict[str, Any] = field(default_factory=dict)

    @property
    def seconds(self) -> float:
        return float(self.params.get("seconds", 0))


NodeType = ActionNode | ConditionNode | NotifyNode | DelayNode


def make_node(node_def: dict[str, Any]) -> NodeType:
    """Factory: parse a YAML node definition dict into a typed Node."""
    node_id = node_def["id"]
    node_type = node_def.get("type", "action")
    params = node_def.get("params", {})
    match node_type:
        case "action":
            return ActionNode(id=node_id, params=params)
        case "condition":
            return ConditionNode(id=node_id, params=params)
        case "notify":
            return NotifyNode(id=node_id, params=params)
        case "delay":
            return DelayNode(id=node_id, params=params)
        case _:
            raise ValueError(f"Unknown node type: {node_type!r} (node id={node_id!r})")
