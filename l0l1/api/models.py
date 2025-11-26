from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class WorkspaceBase(BaseModel):
    name: str = Field(..., description="Workspace name")
    description: Optional[str] = Field(None, description="Workspace description")


class WorkspaceCreate(WorkspaceBase):
    tenant_id: str = Field(..., description="Tenant identifier")


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class Workspace(WorkspaceBase):
    id: str = Field(..., description="Workspace ID")
    tenant_id: str = Field(..., description="Tenant identifier")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QueryValidationRequest(BaseModel):
    query: str = Field(..., description="SQL query to validate")
    schema_context: Optional[str] = Field(None, description="Schema context for validation")
    workspace_id: Optional[str] = Field(None, description="Workspace ID for context")


class QueryValidationResponse(BaseModel):
    is_valid: bool = Field(..., description="Whether the query is valid")
    issues: List[str] = Field(default=[], description="List of issues found")
    suggestions: List[str] = Field(default=[], description="List of improvement suggestions")
    severity: str = Field(default="medium", description="Severity level: low, medium, high")
    pii_detected: List[Dict[str, Any]] = Field(default=[], description="PII entities detected")


class QueryExplanationRequest(BaseModel):
    query: str = Field(..., description="SQL query to explain")
    schema_context: Optional[str] = Field(None, description="Schema context")


class QueryExplanationResponse(BaseModel):
    explanation: str = Field(..., description="Human-readable explanation of the query")
    query_type: Optional[str] = Field(None, description="Type of SQL operation")


class QueryCompletionRequest(BaseModel):
    partial_query: str = Field(..., description="Partial SQL query to complete")
    schema_context: Optional[str] = Field(None, description="Schema context")
    workspace_id: Optional[str] = Field(None, description="Workspace ID for learning context")
    max_suggestions: int = Field(5, description="Maximum number of suggestions", ge=1, le=10)


class QueryCompletionResponse(BaseModel):
    suggestions: List[str] = Field(..., description="List of query completion suggestions")
    learning_applied: bool = Field(False, description="Whether learning data was used")


class QueryCorrectionRequest(BaseModel):
    query: str = Field(..., description="SQL query to correct")
    error_message: Optional[str] = Field(None, description="Error message from database")
    schema_context: Optional[str] = Field(None, description="Schema context")
    workspace_id: Optional[str] = Field(None, description="Workspace ID for learning context")


class QueryCorrectionResponse(BaseModel):
    corrected_query: str = Field(..., description="Corrected SQL query")
    confidence: float = Field(..., description="Confidence score (0-1)")
    learning_applied: bool = Field(False, description="Whether learning data was used")
    suggestions: List[str] = Field(default=[], description="Alternative suggestions")


class PIICheckRequest(BaseModel):
    query: str = Field(..., description="SQL query to check for PII")


class PIICheckResponse(BaseModel):
    pii_detected: bool = Field(..., description="Whether PII was detected")
    entities: List[Dict[str, Any]] = Field(default=[], description="PII entities found")
    anonymized_query: Optional[str] = Field(None, description="Anonymized version of the query")
    anonymizations: List[Dict[str, Any]] = Field(default=[], description="List of anonymizations applied")


class LearningRecordRequest(BaseModel):
    query: str = Field(..., description="Successful SQL query")
    workspace_id: str = Field(..., description="Workspace ID")
    execution_time: float = Field(..., description="Query execution time in seconds")
    result_count: int = Field(..., description="Number of results returned")
    schema_context: Optional[str] = Field(None, description="Schema context")


class LearningStatsResponse(BaseModel):
    total_queries: int = Field(..., description="Total number of learned queries")
    avg_execution_time: float = Field(..., description="Average execution time")
    most_successful: Optional[Dict[str, Any]] = Field(None, description="Most successful query info")
    recent_activity: int = Field(..., description="Recent activity count")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Health status")
    version: str = Field(..., description="API version")
    model_provider: str = Field(..., description="Current AI model provider")
    learning_enabled: bool = Field(..., description="Whether learning is enabled")
    pii_detection_enabled: bool = Field(..., description="Whether PII detection is enabled")


# Database Connection Models
class DatabaseConnectionCreate(BaseModel):
    name: str = Field(..., description="Connection name")
    db_type: str = Field(..., description="Database type (postgresql, mysql, sqlite, duckdb, etc.)")
    host: str = Field("localhost", description="Database host")
    port: int = Field(None, description="Database port (uses default if not specified)")
    database: str = Field(..., description="Database name")
    username: str = Field("", description="Username")
    password: str = Field("", description="Password")
    ssl_enabled: bool = Field(False, description="Enable SSL")
    workspace_id: Optional[str] = Field(None, description="Associated workspace ID")


class DatabaseConnectionUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    ssl_enabled: Optional[bool] = None


class DatabaseConnectionResponse(BaseModel):
    id: str
    name: str
    db_type: str
    host: str
    port: int
    database: str
    username: str
    ssl_enabled: bool
    workspace_id: Optional[str]
    created_at: Optional[str]
    last_connected: Optional[str]
    is_connected: bool


class ConnectionTestResponse(BaseModel):
    success: bool
    message: str
    latency_ms: float
    server_version: Optional[str]


class SchemaIntrospectionResponse(BaseModel):
    connection_id: str
    database: str
    db_type: str
    introspected_at: str
    tables: List[Dict[str, Any]]
    views: List[Dict[str, Any]] = []
    functions: List[Dict[str, Any]] = []


class QueryExecuteRequest(BaseModel):
    query: str = Field(..., description="SQL query to execute (SELECT only)")
    params: Optional[Dict[str, Any]] = Field(None, description="Query parameters")
    limit: int = Field(100, description="Result limit", ge=1, le=1000)


class QueryExecuteResponse(BaseModel):
    success: bool
    columns: List[str] = []
    rows: List[List[Any]] = []
    row_count: int = 0
    execution_time_ms: float = 0
    truncated: bool = False
    error: Optional[str] = None


# Schema Management Models
class SchemaVersionCreate(BaseModel):
    workspace_id: str = Field(..., description="Workspace ID")
    schema_data: Dict[str, Any] = Field(..., description="Schema definition")
    description: str = Field("", description="Version description")
    set_active: bool = Field(True, description="Set as active version")


class SchemaVersionResponse(BaseModel):
    id: str
    version: str
    workspace_id: str
    schema_data: Dict[str, Any]
    description: str
    created_at: Optional[str]
    created_by: Optional[str]
    parent_version: Optional[str]
    is_active: bool
    checksum: str


class SchemaCompareResponse(BaseModel):
    version_1: Dict[str, str]
    version_2: Dict[str, str]
    tables_added: List[Dict[str, Any]]
    tables_removed: List[Dict[str, Any]]
    tables_modified: List[Dict[str, Any]]
    columns_added: List[Dict[str, Any]]
    columns_removed: List[Dict[str, Any]]
    columns_modified: List[Dict[str, Any]]
    indexes_added: List[Dict[str, Any]]
    indexes_removed: List[Dict[str, Any]]


class SchemaMigrationResponse(BaseModel):
    id: str
    change_type: str
    target: str
    details: Dict[str, Any]
    sql_up: str
    sql_down: str
    version_from: Optional[str]
    version_to: Optional[str]
    created_at: str


class SchemaValidationResponse(BaseModel):
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    table_count: int
    total_columns: int


class SchemaExportRequest(BaseModel):
    format: str = Field("json", description="Export format (json, sql)")


class SchemaImportRequest(BaseModel):
    sql: str = Field(..., description="SQL to parse")
    workspace_id: str = Field(..., description="Target workspace ID")


# Learning Pattern Models
class PatternResponse(BaseModel):
    id: str
    query: str
    workspace_id: str
    success_count: int
    execution_time: float
    result_count: int
    last_used: str
    created_at: str
    confidence: float
    schema_context: Optional[str] = None


class PatternListResponse(BaseModel):
    patterns: List[PatternResponse]
    total: int
    limit: int
    offset: int


class PatternUpdateRequest(BaseModel):
    query: Optional[str] = None
    success_count: Optional[int] = None
    execution_time: Optional[float] = None
    schema_context: Optional[str] = None


class PatternBulkDeleteRequest(BaseModel):
    pattern_ids: Optional[List[str]] = None
    workspace_id: Optional[str] = None
    older_than_days: Optional[int] = None


class PatternConfidenceRequest(BaseModel):
    adjustment: float = Field(..., description="Confidence adjustment (-1.0 to 1.0)", ge=-1.0, le=1.0)


class PatternExportResponse(BaseModel):
    data: str
    format: str
    pattern_count: int


class PatternImportRequest(BaseModel):
    data: Dict[str, Any]
    workspace_id: str
    overwrite: bool = False


class PatternImportResponse(BaseModel):
    imported: int
    skipped: int
    total: int