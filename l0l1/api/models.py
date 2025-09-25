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