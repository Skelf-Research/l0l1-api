from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from contextlib import asynccontextmanager

from ..core.config import settings
from ..models.factory import ModelFactory
from ..services.pii_detector import PIIDetector
from ..services.learning_service import LearningService
from ..services.workspace_service import WorkspaceService
from ..services.database_service import DatabaseService
from ..services.schema_service import SchemaService

from .models import (
    QueryValidationRequest, QueryValidationResponse,
    QueryExplanationRequest, QueryExplanationResponse,
    QueryCompletionRequest, QueryCompletionResponse,
    QueryCorrectionRequest, QueryCorrectionResponse,
    PIICheckRequest, PIICheckResponse,
    LearningRecordRequest, LearningStatsResponse,
    Workspace, WorkspaceCreate, WorkspaceUpdate,
    HealthResponse,
    # Database models
    DatabaseConnectionCreate, DatabaseConnectionUpdate, DatabaseConnectionResponse,
    ConnectionTestResponse, SchemaIntrospectionResponse,
    QueryExecuteRequest, QueryExecuteResponse,
    # Schema models
    SchemaVersionCreate, SchemaVersionResponse, SchemaCompareResponse,
    SchemaMigrationResponse, SchemaValidationResponse,
    SchemaExportRequest, SchemaImportRequest,
    # Learning pattern models
    PatternResponse, PatternListResponse, PatternUpdateRequest,
    PatternBulkDeleteRequest, PatternConfidenceRequest,
    PatternExportResponse, PatternImportRequest, PatternImportResponse
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

# Singleton instances for stateful services
_database_service = None
_schema_service = None
_learning_service_instance = None

def get_database_service():
    """Get database service instance (singleton)."""
    global _database_service
    if _database_service is None:
        _database_service = DatabaseService()
    return _database_service

def get_schema_service():
    """Get schema service instance (singleton)."""
    global _schema_service
    if _schema_service is None:
        _schema_service = SchemaService()
    return _schema_service

def get_learning_service_singleton():
    """Get learning service instance (singleton for pattern management)."""
    global _learning_service_instance
    if _learning_service_instance is None:
        _learning_service_instance = LearningService()
    return _learning_service_instance


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
    learning_service: LearningService = Depends(get_learning_service_singleton)
):
    """Get learning statistics."""
    stats = learning_service.get_learning_stats(workspace_id)
    return LearningStatsResponse(**stats)


# =============================================================================
# Database Connection Endpoints
# =============================================================================

@app.get("/databases/supported")
async def get_supported_databases(
    db_service: DatabaseService = Depends(get_database_service)
):
    """Get list of supported database types."""
    return db_service.get_supported_databases()


@app.post("/databases", response_model=DatabaseConnectionResponse, status_code=201)
async def create_database_connection(
    connection: DatabaseConnectionCreate,
    db_service: DatabaseService = Depends(get_database_service)
):
    """Create a new database connection."""
    try:
        conn = await db_service.create_connection(
            name=connection.name,
            db_type=connection.db_type,
            host=connection.host,
            port=connection.port,
            database=connection.database,
            username=connection.username,
            password=connection.password,
            ssl_enabled=connection.ssl_enabled,
            workspace_id=connection.workspace_id
        )
        return DatabaseConnectionResponse(**conn.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/databases", response_model=List[DatabaseConnectionResponse])
async def list_database_connections(
    workspace_id: Optional[str] = None,
    db_service: DatabaseService = Depends(get_database_service)
):
    """List all database connections."""
    connections = await db_service.list_connections(workspace_id)
    return [DatabaseConnectionResponse(**c.to_dict()) for c in connections]


@app.get("/databases/{connection_id}", response_model=DatabaseConnectionResponse)
async def get_database_connection(
    connection_id: str,
    db_service: DatabaseService = Depends(get_database_service)
):
    """Get a database connection by ID."""
    conn = await db_service.get_connection(connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    return DatabaseConnectionResponse(**conn.to_dict())


@app.put("/databases/{connection_id}", response_model=DatabaseConnectionResponse)
async def update_database_connection(
    connection_id: str,
    update: DatabaseConnectionUpdate,
    db_service: DatabaseService = Depends(get_database_service)
):
    """Update a database connection."""
    conn = await db_service.update_connection(connection_id, **update.model_dump(exclude_none=True))
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    return DatabaseConnectionResponse(**conn.to_dict())


@app.delete("/databases/{connection_id}", status_code=204)
async def delete_database_connection(
    connection_id: str,
    db_service: DatabaseService = Depends(get_database_service)
):
    """Delete a database connection."""
    success = await db_service.delete_connection(connection_id)
    if not success:
        raise HTTPException(status_code=404, detail="Connection not found")


@app.post("/databases/{connection_id}/test", response_model=ConnectionTestResponse)
async def test_database_connection(
    connection_id: str,
    db_service: DatabaseService = Depends(get_database_service)
):
    """Test a database connection."""
    try:
        result = await db_service.test_connection(connection_id)
        return ConnectionTestResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/databases/{connection_id}/schema", response_model=SchemaIntrospectionResponse)
async def introspect_database_schema(
    connection_id: str,
    db_service: DatabaseService = Depends(get_database_service)
):
    """Introspect database schema."""
    try:
        schema = await db_service.introspect_schema(connection_id)
        return SchemaIntrospectionResponse(**schema)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/databases/{connection_id}/query", response_model=QueryExecuteResponse)
async def execute_database_query(
    connection_id: str,
    request: QueryExecuteRequest,
    db_service: DatabaseService = Depends(get_database_service)
):
    """Execute a SELECT query on the database."""
    try:
        result = await db_service.execute_query(
            connection_id,
            request.query,
            request.params,
            request.limit
        )
        return QueryExecuteResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Schema Management Endpoints
# =============================================================================

@app.post("/schemas", response_model=SchemaVersionResponse, status_code=201)
async def create_schema_version(
    schema: SchemaVersionCreate,
    schema_service: SchemaService = Depends(get_schema_service)
):
    """Create a new schema version."""
    version = await schema_service.create_schema_version(
        workspace_id=schema.workspace_id,
        schema_data=schema.schema_data,
        description=schema.description,
        set_active=schema.set_active
    )
    return SchemaVersionResponse(**version.to_dict())


@app.get("/schemas", response_model=List[SchemaVersionResponse])
async def list_schema_versions(
    workspace_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    schema_service: SchemaService = Depends(get_schema_service)
):
    """List schema versions for a workspace."""
    versions = await schema_service.list_versions(workspace_id, limit, offset)
    return [SchemaVersionResponse(**v.to_dict()) for v in versions]


@app.get("/schemas/active/{workspace_id}", response_model=SchemaVersionResponse)
async def get_active_schema_version(
    workspace_id: str,
    schema_service: SchemaService = Depends(get_schema_service)
):
    """Get the active schema version for a workspace."""
    version = await schema_service.get_active_version(workspace_id)
    if not version:
        raise HTTPException(status_code=404, detail="No active schema version found")
    return SchemaVersionResponse(**version.to_dict())


@app.get("/schemas/{version_id}", response_model=SchemaVersionResponse)
async def get_schema_version(
    version_id: str,
    schema_service: SchemaService = Depends(get_schema_service)
):
    """Get a schema version by ID."""
    version = await schema_service.get_schema_version(version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Schema version not found")
    return SchemaVersionResponse(**version.to_dict())


@app.post("/schemas/{version_id}/activate", response_model=SchemaVersionResponse)
async def activate_schema_version(
    version_id: str,
    workspace_id: str,
    schema_service: SchemaService = Depends(get_schema_service)
):
    """Set a schema version as active."""
    success = await schema_service.set_active_version(workspace_id, version_id)
    if not success:
        raise HTTPException(status_code=400, detail="Could not activate schema version")
    version = await schema_service.get_schema_version(version_id)
    return SchemaVersionResponse(**version.to_dict())


@app.post("/schemas/compare", response_model=SchemaCompareResponse)
async def compare_schema_versions(
    version_id_1: str,
    version_id_2: str,
    schema_service: SchemaService = Depends(get_schema_service)
):
    """Compare two schema versions."""
    try:
        diff = await schema_service.compare_versions(version_id_1, version_id_2)
        return SchemaCompareResponse(**diff)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/schemas/migrate", response_model=List[SchemaMigrationResponse])
async def generate_schema_migration(
    from_version_id: str,
    to_version_id: str,
    schema_service: SchemaService = Depends(get_schema_service)
):
    """Generate migration SQL between two schema versions."""
    try:
        migrations = await schema_service.generate_migration(from_version_id, to_version_id)
        return [SchemaMigrationResponse(**m.to_dict()) for m in migrations]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/schemas/validate", response_model=SchemaValidationResponse)
async def validate_schema(
    schema_data: dict,
    schema_service: SchemaService = Depends(get_schema_service)
):
    """Validate a schema definition."""
    result = await schema_service.validate_schema(schema_data)
    return SchemaValidationResponse(**result)


@app.get("/schemas/{version_id}/export")
async def export_schema(
    version_id: str,
    format: str = Query("json", regex="^(json|sql)$"),
    schema_service: SchemaService = Depends(get_schema_service)
):
    """Export schema in JSON or SQL format."""
    try:
        content = await schema_service.export_schema(version_id, format)
        media_type = "application/json" if format == "json" else "text/plain"
        return PlainTextResponse(content=content, media_type=media_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/schemas/import")
async def import_schema_from_sql(
    request: SchemaImportRequest,
    schema_service: SchemaService = Depends(get_schema_service)
):
    """Import schema from SQL statements."""
    result = await schema_service.import_schema_from_sql(request.sql, request.workspace_id)
    return result


# =============================================================================
# Learning Pattern Management Endpoints
# =============================================================================

@app.get("/learning/patterns", response_model=PatternListResponse)
async def list_patterns(
    workspace_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("last_used", regex="^(last_used|success_count|execution_time|created_at)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    learning_service: LearningService = Depends(get_learning_service_singleton)
):
    """List learned patterns with pagination."""
    result = learning_service.list_patterns(workspace_id, limit, offset, sort_by, sort_order)
    return PatternListResponse(**result)


@app.get("/learning/patterns/{pattern_id}", response_model=PatternResponse)
async def get_pattern(
    pattern_id: str,
    learning_service: LearningService = Depends(get_learning_service_singleton)
):
    """Get a specific pattern by ID."""
    pattern = learning_service.get_pattern(pattern_id)
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    return PatternResponse(**pattern)


@app.put("/learning/patterns/{pattern_id}", response_model=PatternResponse)
async def update_pattern(
    pattern_id: str,
    update: PatternUpdateRequest,
    learning_service: LearningService = Depends(get_learning_service_singleton)
):
    """Update a pattern."""
    pattern = learning_service.update_pattern(pattern_id, update.model_dump(exclude_none=True))
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    return PatternResponse(**pattern)


@app.delete("/learning/patterns/{pattern_id}", status_code=204)
async def delete_pattern(
    pattern_id: str,
    learning_service: LearningService = Depends(get_learning_service_singleton)
):
    """Delete a pattern."""
    success = learning_service.delete_pattern(pattern_id)
    if not success:
        raise HTTPException(status_code=404, detail="Pattern not found")


@app.post("/learning/patterns/bulk-delete")
async def bulk_delete_patterns(
    request: PatternBulkDeleteRequest,
    learning_service: LearningService = Depends(get_learning_service_singleton)
):
    """Bulk delete patterns."""
    deleted = learning_service.bulk_delete_patterns(
        pattern_ids=request.pattern_ids,
        workspace_id=request.workspace_id,
        older_than_days=request.older_than_days
    )
    return {"deleted_count": deleted}


@app.post("/learning/patterns/{pattern_id}/confidence", response_model=PatternResponse)
async def adjust_pattern_confidence(
    pattern_id: str,
    request: PatternConfidenceRequest,
    learning_service: LearningService = Depends(get_learning_service_singleton)
):
    """Adjust a pattern's confidence score."""
    pattern = learning_service.adjust_confidence(pattern_id, request.adjustment)
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    return PatternResponse(**pattern)


@app.get("/learning/export", response_model=PatternExportResponse)
async def export_patterns(
    workspace_id: Optional[str] = None,
    format: str = Query("json", regex="^json$"),
    learning_service: LearningService = Depends(get_learning_service_singleton)
):
    """Export learned patterns."""
    data = learning_service.export_patterns(workspace_id, format)
    patterns_result = learning_service.list_patterns(workspace_id)
    return PatternExportResponse(
        data=data,
        format=format,
        pattern_count=patterns_result["total"]
    )


@app.post("/learning/import", response_model=PatternImportResponse)
async def import_patterns(
    request: PatternImportRequest,
    learning_service: LearningService = Depends(get_learning_service_singleton)
):
    """Import patterns from backup."""
    result = await learning_service.import_patterns(
        request.data,
        request.workspace_id,
        request.overwrite
    )
    return PatternImportResponse(**result)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "l0l1.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )