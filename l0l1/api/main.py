from typing import List
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from ..core.config import settings
from ..models.factory import ModelFactory
from ..services.pii_detector import PIIDetector
from ..services.learning_service import LearningService
from ..services.workspace_service import WorkspaceService

from .models import (
    QueryValidationRequest, QueryValidationResponse,
    QueryExplanationRequest, QueryExplanationResponse,
    QueryCompletionRequest, QueryCompletionResponse,
    QueryCorrectionRequest, QueryCorrectionResponse,
    PIICheckRequest, PIICheckResponse,
    LearningRecordRequest, LearningStatsResponse,
    Workspace, WorkspaceCreate, WorkspaceUpdate,
    HealthResponse
)
from . import jupyter
from . import ui


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("🚀 Starting l0l1 API server...")
    try:
        # Initialize model to check connectivity
        model = ModelFactory.get_default_model()
        print(f"✅ AI model initialized: {settings.default_provider}")
    except Exception as e:
        print(f"⚠️ Warning: Could not initialize AI model: {e}")

    yield

    # Shutdown
    print("🛑 Shutting down l0l1 API server...")


app = FastAPI(
    title="l0l1 SQL Analysis API",
    description="SQL Analysis and Validation Library with AI-powered features",
    version="0.2.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Include Jupyter and UI routers for integration
app.include_router(jupyter.router)
app.include_router(ui.router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependencies
def get_model():
    """Get AI model instance."""
    return ModelFactory.get_default_model()

def get_pii_detector():
    """Get PII detector instance."""
    return PIIDetector()

def get_learning_service():
    """Get learning service instance."""
    return LearningService()

def get_workspace_service():
    """Get workspace service instance."""
    return WorkspaceService()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="0.2.0",
        model_provider=settings.default_provider,
        learning_enabled=settings.enable_learning,
        pii_detection_enabled=settings.enable_pii_detection
    )


# Workspace Management
@app.get("/workspaces", response_model=List[Workspace])
async def list_workspaces(
    tenant_id: str,
    workspace_service: WorkspaceService = Depends(get_workspace_service)
):
    """List all workspaces for a tenant."""
    return await workspace_service.list_workspaces(tenant_id)


@app.post("/workspaces", response_model=Workspace, status_code=201)
async def create_workspace(
    workspace: WorkspaceCreate,
    workspace_service: WorkspaceService = Depends(get_workspace_service)
):
    """Create a new workspace."""
    return await workspace_service.create_workspace(workspace)


@app.get("/workspaces/{workspace_id}", response_model=Workspace)
async def get_workspace(
    workspace_id: str,
    workspace_service: WorkspaceService = Depends(get_workspace_service)
):
    """Get workspace by ID."""
    workspace = await workspace_service.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


@app.put("/workspaces/{workspace_id}", response_model=Workspace)
async def update_workspace(
    workspace_id: str,
    workspace_update: WorkspaceUpdate,
    workspace_service: WorkspaceService = Depends(get_workspace_service)
):
    """Update workspace."""
    workspace = await workspace_service.update_workspace(workspace_id, workspace_update)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


@app.delete("/workspaces/{workspace_id}", status_code=204)
async def delete_workspace(
    workspace_id: str,
    workspace_service: WorkspaceService = Depends(get_workspace_service)
):
    """Delete workspace."""
    success = await workspace_service.delete_workspace(workspace_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workspace not found")


# SQL Analysis Endpoints
@app.post("/sql/validate", response_model=QueryValidationResponse)
async def validate_query(
    request: QueryValidationRequest,
    model=Depends(get_model),
    pii_detector: PIIDetector = Depends(get_pii_detector)
):
    """Validate SQL query."""
    try:
        # Check for PII
        pii_detected = []
        if settings.enable_pii_detection:
            pii_findings = pii_detector.detect_pii(request.query)
            pii_detected = pii_findings

        # Validate query
        validation_result = await model.validate_sql_query(
            request.query,
            request.schema_context
        )

        return QueryValidationResponse(
            is_valid=validation_result.get("is_valid", True),
            issues=validation_result.get("issues", []),
            suggestions=validation_result.get("suggestions", []),
            severity=validation_result.get("severity", "medium"),
            pii_detected=pii_detected
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")


@app.post("/sql/explain", response_model=QueryExplanationResponse)
async def explain_query(
    request: QueryExplanationRequest,
    model=Depends(get_model)
):
    """Explain SQL query."""
    try:
        explanation = await model.explain_sql_query(
            request.query,
            request.schema_context
        )
        return QueryExplanationResponse(explanation=explanation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation error: {str(e)}")


@app.post("/sql/complete", response_model=QueryCompletionResponse)
async def complete_query(
    request: QueryCompletionRequest,
    model=Depends(get_model),
    learning_service: LearningService = Depends(get_learning_service)
):
    """Complete partial SQL query."""
    try:
        if request.workspace_id and settings.enable_learning:
            # Use learning service for smarter completions
            suggestions = await learning_service.get_query_suggestions(
                request.partial_query,
                request.workspace_id,
                request.schema_context
            )
            learning_applied = len(suggestions) > 0
        else:
            # Fallback to AI completion
            completion = await model.complete_sql_query(
                request.partial_query,
                request.schema_context
            )
            suggestions = [completion]
            learning_applied = False

        # Limit suggestions
        suggestions = suggestions[:request.max_suggestions]

        return QueryCompletionResponse(
            suggestions=suggestions,
            learning_applied=learning_applied
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Completion error: {str(e)}")


@app.post("/sql/correct", response_model=QueryCorrectionResponse)
async def correct_query(
    request: QueryCorrectionRequest,
    model=Depends(get_model),
    learning_service: LearningService = Depends(get_learning_service)
):
    """Correct SQL query."""
    try:
        if request.workspace_id and settings.enable_learning:
            # Use learning service for smarter corrections
            improvement = await learning_service.improve_query_with_learning(
                request.query,
                request.workspace_id,
                request.error_message,
                request.schema_context
            )
            return QueryCorrectionResponse(
                corrected_query=improvement["improved_query"],
                confidence=improvement["confidence"],
                learning_applied=improvement["learning_applied"],
                suggestions=improvement["suggestions"]
            )
        else:
            # Fallback to AI correction
            corrected = await model.correct_sql_query(
                request.query,
                request.error_message,
                request.schema_context
            )
            return QueryCorrectionResponse(
                corrected_query=corrected,
                confidence=0.7,
                learning_applied=False,
                suggestions=[]
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Correction error: {str(e)}")


@app.post("/sql/check-pii", response_model=PIICheckResponse)
async def check_pii(
    request: PIICheckRequest,
    pii_detector: PIIDetector = Depends(get_pii_detector)
):
    """Check SQL query for PII."""
    try:
        pii_findings = pii_detector.detect_pii(request.query)
        pii_detected = len(pii_findings) > 0

        anonymized_query = None
        anonymizations = []
        if pii_detected:
            anonymized_query, anonymizations = pii_detector.anonymize_sql(request.query)

        return PIICheckResponse(
            pii_detected=pii_detected,
            entities=pii_findings,
            anonymized_query=anonymized_query,
            anonymizations=anonymizations
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PII check error: {str(e)}")


# Learning Endpoints
@app.post("/learning/record", status_code=201)
async def record_successful_query(
    request: LearningRecordRequest,
    background_tasks: BackgroundTasks,
    learning_service: LearningService = Depends(get_learning_service)
):
    """Record a successful query for learning."""
    if not settings.enable_learning:
        raise HTTPException(status_code=400, detail="Learning is disabled")

    background_tasks.add_task(
        learning_service.record_successful_query,
        request.workspace_id,
        request.query,
        request.execution_time,
        request.result_count,
        request.schema_context
    )
    return {"message": "Query recorded for learning"}


@app.get("/learning/stats", response_model=LearningStatsResponse)
async def get_learning_stats(
    workspace_id: str = None,
    learning_service: LearningService = Depends(get_learning_service)
):
    """Get learning statistics."""
    stats = learning_service.get_learning_stats(workspace_id)
    return LearningStatsResponse(**stats)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "l0l1.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )