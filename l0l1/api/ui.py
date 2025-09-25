from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ..integrations.ui.session import UISession
from ..integrations.ui.components import SQLCellRenderer, NotebookRenderer

router = APIRouter(prefix="/ui", tags=["ui"])

# In-memory session storage - replace with persistent storage in production
sessions: Dict[str, UISession] = {}


class CreateSessionRequest(BaseModel):
    workspace_id: str = "default"
    tenant_id: str = "default"
    schema_context: Optional[str] = None
    metadata: Dict[str, Any] = {}


class UpdateSessionRequest(BaseModel):
    schema_context: Optional[str] = None
    metadata: Dict[str, Any] = {}


class CreateCellRequest(BaseModel):
    cell_type: str = "sql"
    source: str = ""


class UpdateCellRequest(BaseModel):
    source: str
    options: Optional[Dict[str, Any]] = None


class ExecuteCellRequest(BaseModel):
    session_id: str
    cell_id: str
    source: str
    options: Dict[str, Any] = {}


class MoveCellRequest(BaseModel):
    new_index: int


class RenderRequest(BaseModel):
    analysis_results: Dict[str, Any]
    format: str = "vue"  # vue, skeleton, tailwind


@router.post("/sessions")
async def create_session(request: CreateSessionRequest):
    """Create a new UI session."""
    session = UISession(
        workspace_id=request.workspace_id,
        tenant_id=request.tenant_id,
        schema_context=request.schema_context,
        metadata=request.metadata
    )
    sessions[session.session_id] = session
    return {"session_id": session.session_id}


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session details."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    return {
        "session": session.export_notebook(),
        "stats": session.get_session_stats()
    }


@router.put("/sessions/{session_id}")
async def update_session(session_id: str, request: UpdateSessionRequest):
    """Update session metadata."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    if request.schema_context is not None:
        session.schema_context = request.schema_context
    session.metadata.update(request.metadata)

    return {"status": "updated"}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    del sessions[session_id]
    return {"status": "deleted"}


@router.post("/sessions/{session_id}/cells")
async def create_cell(session_id: str, request: CreateCellRequest):
    """Add a new cell to the session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    cell_id = session.add_cell(request.cell_type, request.source)
    return {"cell_id": cell_id}


@router.get("/sessions/{session_id}/cells/{cell_id}")
async def get_cell(session_id: str, cell_id: str):
    """Get a specific cell."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    cell = session.get_cell(cell_id)
    if not cell:
        raise HTTPException(status_code=404, detail="Cell not found")

    return {"cell": cell}


@router.put("/sessions/{session_id}/cells/{cell_id}")
async def update_cell(session_id: str, cell_id: str, request: UpdateCellRequest):
    """Update cell content."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    success = session.update_cell(cell_id, request.source, request.options)
    if not success:
        raise HTTPException(status_code=404, detail="Cell not found")

    return {"status": "updated"}


@router.delete("/sessions/{session_id}/cells/{cell_id}")
async def delete_cell(session_id: str, cell_id: str):
    """Delete a cell."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    success = session.delete_cell(cell_id)
    if not success:
        raise HTTPException(status_code=404, detail="Cell not found")

    return {"status": "deleted"}


@router.put("/sessions/{session_id}/cells/{cell_id}/move")
async def move_cell(session_id: str, cell_id: str, request: MoveCellRequest):
    """Move a cell to a new position."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    success = session.move_cell(cell_id, request.new_index)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid move operation")

    return {"status": "moved"}


@router.post("/sessions/{session_id}/cells/{cell_id}/execute")
async def execute_cell_ui(session_id: str, cell_id: str, request: ExecuteCellRequest):
    """Execute a cell and return UI-formatted results."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    cell = session.get_cell(cell_id)
    if not cell:
        raise HTTPException(status_code=404, detail="Cell not found")

    # Execute the cell using the jupyter endpoint
    from .jupyter import router as jupyter_router
    from .jupyter import JupyterCellRequest

    jupyter_request = JupyterCellRequest(
        cell_type=cell["cell_type"],
        source=request.source,
        workspace_id=session.workspace_id,
        schema_context=session.schema_context,
        options=request.options
    )

    # This would normally be called as a sub-request, but for simplicity:
    from ..api.jupyter import execute_cell
    from ..models.factory import ModelFactory
    from ..services.pii_detector import PIIDetector
    from ..services.learning_service import LearningService
    from fastapi import BackgroundTasks

    background_tasks = BackgroundTasks()
    model = ModelFactory.get_default_model()
    pii_detector = PIIDetector()
    learning_service = LearningService()

    result = await execute_cell(
        jupyter_request, background_tasks, model, pii_detector, learning_service
    )

    # Update session with execution results
    session.execute_cell(cell_id, result.outputs)

    return {
        "execution_result": result,
        "cell_id": cell_id,
        "session_id": session_id
    }


@router.delete("/sessions/{session_id}/outputs")
async def clear_all_outputs(session_id: str):
    """Clear all cell outputs in the session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    session.clear_all_outputs()
    return {"status": "cleared"}


@router.get("/sessions/{session_id}/export")
async def export_notebook(session_id: str):
    """Export session as notebook format."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    return session.export_notebook()


@router.post("/sessions/{session_id}/import")
async def import_notebook(session_id: str, notebook_data: Dict[str, Any]):
    """Import notebook data into session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    success = session.import_notebook(notebook_data)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid notebook format")

    return {"status": "imported"}


@router.post("/render")
async def render_analysis_results(request: RenderRequest):
    """Render analysis results in different UI formats."""
    renderer = SQLCellRenderer()

    if request.format == "vue":
        rendered = renderer.render_to_vue_component(request.analysis_results)
    elif request.format == "skeleton":
        rendered = renderer.render_to_skeleton_ui(request.analysis_results)
    elif request.format == "tailwind":
        # Extract component type from results for class generation
        component_type = "query-display"  # Default
        if "pii" in request.analysis_results.get("results", {}):
            component_type = "pii-detection"
        elif "validation" in request.analysis_results.get("results", {}):
            component_type = "validation-result"

        rendered = {
            "classes": renderer.generate_tailwind_classes(component_type),
            "data": request.analysis_results
        }
    else:
        raise HTTPException(status_code=400, detail="Unsupported render format")

    return {"rendered": rendered}


@router.get("/templates/cell")
async def get_cell_template(cell_type: str = "sql"):
    """Get a template for creating new cells."""
    template = NotebookRenderer.create_cell_template(cell_type)
    return {"template": template}


@router.get("/templates/notebook")
async def get_notebook_template(workspace_id: str, title: str = "New Notebook"):
    """Get a template for creating new notebooks."""
    template = NotebookRenderer.create_notebook_template(workspace_id, title)
    return {"template": template}


@router.get("/toolbar")
async def get_notebook_toolbar():
    """Get toolbar configuration for notebook interface."""
    toolbar = NotebookRenderer.render_notebook_toolbar()
    return {"toolbar": toolbar}


@router.get("/sessions")
async def list_sessions(workspace_id: Optional[str] = None, tenant_id: Optional[str] = None):
    """List active sessions with optional filtering."""
    filtered_sessions = []

    for session in sessions.values():
        if workspace_id and session.workspace_id != workspace_id:
            continue
        if tenant_id and session.tenant_id != tenant_id:
            continue

        filtered_sessions.append({
            "session_id": session.session_id,
            "workspace_id": session.workspace_id,
            "tenant_id": session.tenant_id,
            "created_at": session.created_at.isoformat(),
            "cell_count": len(session.cells),
            "execution_count": session.execution_count
        })

    return {"sessions": filtered_sessions}