"""Workflows router – trigger DAG workflows via REST."""

from __future__ import annotations

from crm_core.dag.engine import DAGEngine, RunResult
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from crm_api.deps import get_dag_engine

router = APIRouter()


class WorkflowTrigger(BaseModel):
    context: dict = {}


@router.post("/{workflow_id}/run", response_model=dict)
def run_workflow(
    workflow_id: str,
    payload: WorkflowTrigger,
    engine: DAGEngine = Depends(get_dag_engine),
) -> dict:
    """Trigger a registered DAG workflow with the given context."""
    try:
        result: RunResult = engine.run(workflow_id, payload.context)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found") from exc
    return {
        "workflow_id": result.workflow_id,
        "run_id": result.run_id,
        "status": result.status,
        "steps": len(result.steps),
        "error": result.error,
    }
