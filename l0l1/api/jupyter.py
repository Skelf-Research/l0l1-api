from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel

from ..models.factory import ModelFactory
from ..services.pii_detector import PIIDetector
from ..services.learning_service import LearningService
from ..core.config import settings

router = APIRouter(prefix="/jupyter", tags=["jupyter"])


class JupyterCellRequest(BaseModel):
    """Request model for executing Jupyter-like cells."""
    cell_type: str = "sql"  # sql, markdown, python
    source: str
    workspace_id: Optional[str] = None
    schema_context: Optional[str] = None
    options: Dict[str, Any] = {}


class JupyterCellOutput(BaseModel):
    """Response model for Jupyter cell execution."""
    output_type: str  # display_data, stream, error
    data: Dict[str, Any]
    metadata: Dict[str, Any] = {}


class JupyterCellResponse(BaseModel):
    """Response for Jupyter cell execution."""
    execution_count: int
    outputs: List[JupyterCellOutput]
    status: str  # ok, error
    execution_time_ms: int


def get_model():
    return ModelFactory.get_default_model()

def get_pii_detector():
    return PIIDetector()

def get_learning_service():
    return LearningService()


@router.post("/execute-cell", response_model=JupyterCellResponse)
async def execute_cell(
    request: JupyterCellRequest,
    background_tasks: BackgroundTasks,
    model=Depends(get_model),
    pii_detector: PIIDetector = Depends(get_pii_detector),
    learning_service: LearningService = Depends(get_learning_service)
):
    """Execute a Jupyter-like cell and return rich output."""
    import time
    start_time = time.time()

    outputs = []
    status = "ok"

    try:
        if request.cell_type == "sql":
            # Process SQL cell
            outputs = await _process_sql_cell(
                request, model, pii_detector, learning_service, background_tasks
            )
        elif request.cell_type == "markdown":
            # Process markdown cell
            outputs = [JupyterCellOutput(
                output_type="display_data",
                data={
                    "text/html": f"<div class='markdown-cell'>{request.source}</div>",
                    "text/markdown": request.source
                }
            )]
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported cell type: {request.cell_type}")

    except Exception as e:
        status = "error"
        outputs = [JupyterCellOutput(
            output_type="error",
            data={
                "ename": type(e).__name__,
                "evalue": str(e),
                "traceback": [str(e)]
            }
        )]

    execution_time_ms = int((time.time() - start_time) * 1000)

    return JupyterCellResponse(
        execution_count=1,  # In a real implementation, this would be tracked per session
        outputs=outputs,
        status=status,
        execution_time_ms=execution_time_ms
    )


async def _process_sql_cell(
    request: JupyterCellRequest,
    model,
    pii_detector: PIIDetector,
    learning_service: LearningService,
    background_tasks: BackgroundTasks
) -> List[JupyterCellOutput]:
    """Process a SQL cell and return rich outputs."""
    outputs = []
    sql_query = request.source.strip()

    # Get options
    options = request.options
    validate = options.get("validate", True)
    explain = options.get("explain", False)
    check_pii = options.get("check_pii", settings.enable_pii_detection)
    complete = options.get("complete", False)
    anonymize = options.get("anonymize", False)

    # Create main output structure
    analysis_results = {
        "query": sql_query,
        "results": {}
    }

    # PII Detection
    if check_pii:
        pii_findings = pii_detector.detect_pii(sql_query)
        if pii_findings:
            analysis_results["results"]["pii"] = {
                "detected": True,
                "entities": pii_findings,
                "severity": "warning"
            }

            if anonymize:
                anonymized_query, anonymizations = pii_detector.anonymize_sql(sql_query)
                analysis_results["results"]["pii"]["anonymized_query"] = anonymized_query
                analysis_results["results"]["pii"]["anonymizations"] = anonymizations
        else:
            analysis_results["results"]["pii"] = {
                "detected": False,
                "message": "No PII detected"
            }

    # Validation
    if validate:
        try:
            validation_result = await model.validate_sql_query(
                sql_query, request.schema_context
            )
            analysis_results["results"]["validation"] = validation_result
        except Exception as e:
            analysis_results["results"]["validation"] = {
                "error": str(e),
                "is_valid": False
            }

    # Explanation
    if explain:
        try:
            explanation = await model.explain_sql_query(
                sql_query, request.schema_context
            )
            analysis_results["results"]["explanation"] = {
                "text": explanation
            }
        except Exception as e:
            analysis_results["results"]["explanation"] = {
                "error": str(e)
            }

    # Query Completion/Suggestions
    if complete and request.workspace_id:
        try:
            suggestions = await learning_service.get_query_suggestions(
                sql_query, request.workspace_id, request.schema_context
            )
            analysis_results["results"]["suggestions"] = {
                "completions": suggestions,
                "learning_applied": len(suggestions) > 0
            }
        except Exception as e:
            analysis_results["results"]["suggestions"] = {
                "error": str(e)
            }

    # Learning Statistics
    if request.workspace_id and settings.enable_learning:
        stats = learning_service.get_learning_stats(request.workspace_id)
        analysis_results["results"]["learning_stats"] = stats

    # Create rich HTML output
    html_output = _generate_html_output(analysis_results)

    # Add main display output
    outputs.append(JupyterCellOutput(
        output_type="display_data",
        data={
            "text/html": html_output,
            "application/json": analysis_results,
            "text/plain": f"SQL Analysis Results for: {sql_query[:100]}..."
        },
        metadata={
            "l0l1": {
                "analysis_type": "sql",
                "workspace_id": request.workspace_id,
                "has_pii": analysis_results["results"].get("pii", {}).get("detected", False),
                "is_valid": analysis_results["results"].get("validation", {}).get("is_valid", True)
            }
        }
    ))

    return outputs


def _generate_html_output(analysis_results: Dict[str, Any]) -> str:
    """Generate rich HTML output for the UI."""
    query = analysis_results["query"]
    results = analysis_results["results"]

    html = f"""
    <div class="l0l1-analysis-output" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <div class="query-display" style="background: #f8f9fa; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
            <h4 style="margin: 0 0 12px 0; color: #495057; font-size: 14px; font-weight: 600;">SQL Query</h4>
            <pre style="background: #2d3748; color: #e2e8f0; padding: 12px; border-radius: 6px; overflow-x: auto; margin: 0; font-size: 13px; line-height: 1.4;"><code>{query}</code></pre>
        </div>
    """

    # PII Results
    if "pii" in results:
        pii_data = results["pii"]
        if pii_data["detected"]:
            html += f"""
            <div class="pii-results" style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                <h4 style="margin: 0 0 12px 0; color: #856404; font-size: 14px; font-weight: 600;">⚠️ PII Detected</h4>
                <div class="pii-entities">
            """
            for entity in pii_data["entities"]:
                html += f"""
                    <div style="margin-bottom: 8px; padding: 8px; background: rgba(255, 193, 7, 0.1); border-radius: 4px;">
                        <strong>{entity['entity_type']}</strong>: <code>{entity['text']}</code>
                        <span style="color: #6c757d; font-size: 12px;">(confidence: {entity['confidence']:.2f})</span>
                    </div>
                """

            if "anonymized_query" in pii_data:
                html += f"""
                </div>
                <div class="anonymized-query" style="margin-top: 12px;">
                    <h5 style="margin: 0 0 8px 0; color: #856404; font-size: 13px;">Anonymized Query:</h5>
                    <pre style="background: #2d3748; color: #e2e8f0; padding: 12px; border-radius: 6px; margin: 0; font-size: 13px;"><code>{pii_data['anonymized_query']}</code></pre>
                </div>
                """
            html += "</div>"
        else:
            html += f"""
            <div class="pii-results" style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                <div style="color: #155724; font-weight: 500;">✅ No PII detected</div>
            </div>
            """

    # Validation Results
    if "validation" in results:
        validation = results["validation"]
        if validation.get("is_valid", True):
            html += f"""
            <div class="validation-results" style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                <div style="color: #155724; font-weight: 500;">✅ Query is valid</div>
            </div>
            """
        else:
            severity_colors = {
                "low": "#ffc107",
                "medium": "#fd7e14",
                "high": "#dc3545"
            }
            severity = validation.get("severity", "medium")
            color = severity_colors.get(severity, "#fd7e14")

            html += f"""
            <div class="validation-results" style="background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                <h4 style="margin: 0 0 12px 0; color: #721c24; font-size: 14px; font-weight: 600;">❌ Validation Issues</h4>
                <div style="margin-bottom: 12px;">
                    <span style="background: {color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; text-transform: uppercase; font-weight: 600;">
                        {severity} severity
                    </span>
                </div>
            """

            if validation.get("issues"):
                html += "<div class='issues'>"
                for issue in validation["issues"]:
                    html += f"<div style='margin-bottom: 6px;'>• {issue}</div>"
                html += "</div>"

            if validation.get("suggestions"):
                html += "<div style='margin-top: 12px;'><strong>Suggestions:</strong>"
                for suggestion in validation["suggestions"]:
                    html += f"<div style='margin-bottom: 6px; color: #0066cc;'>• {suggestion}</div>"
                html += "</div>"

            html += "</div>"

    # Explanation
    if "explanation" in results:
        explanation = results["explanation"]
        if "error" not in explanation:
            html += f"""
            <div class="explanation-results" style="background: #e3f2fd; border: 1px solid #90caf9; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                <h4 style="margin: 0 0 12px 0; color: #0d47a1; font-size: 14px; font-weight: 600;">📝 Query Explanation</h4>
                <div style="line-height: 1.6; color: #1565c0;">{explanation['text'].replace('\n', '<br>')}</div>
            </div>
            """

    # Suggestions
    if "suggestions" in results:
        suggestions = results["suggestions"]
        if "error" not in suggestions and suggestions.get("completions"):
            html += f"""
            <div class="suggestions-results" style="background: #e8f5e8; border: 1px solid #4caf50; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                <h4 style="margin: 0 0 12px 0; color: #2e7d32; font-size: 14px; font-weight: 600;">💡 Query Suggestions</h4>
            """

            for i, suggestion in enumerate(suggestions["completions"][:3], 1):
                html += f"""
                <div style="margin-bottom: 12px;">
                    <div style="font-weight: 500; margin-bottom: 4px;">Option {i}:</div>
                    <pre style="background: #2d3748; color: #e2e8f0; padding: 12px; border-radius: 6px; margin: 0; font-size: 13px; overflow-x: auto;"><code>{suggestion}</code></pre>
                </div>
                """
            html += "</div>"

    # Learning Stats
    if "learning_stats" in results:
        stats = results["learning_stats"]
        if stats["total_queries"] > 0:
            html += f"""
            <div class="learning-stats" style="background: #f3e5f5; border: 1px solid #ce93d8; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                <h4 style="margin: 0 0 12px 0; color: #7b1fa2; font-size: 14px; font-weight: 600;">🧠 Learning Statistics</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; font-size: 13px;">
                    <div><strong>Learned Queries:</strong> {stats["total_queries"]}</div>
                    <div><strong>Avg Execution:</strong> {stats["avg_execution_time"]:.3f}s</div>
                    <div><strong>Recent Activity:</strong> {stats["recent_activity"]}</div>
                </div>
            </div>
            """

    html += "</div>"
    return html


@router.get("/kernel-info")
async def get_kernel_info():
    """Get information about the l0l1 'kernel'."""
    return {
        "name": "l0l1-sql",
        "version": "0.2.0",
        "language": "sql",
        "capabilities": {
            "validation": True,
            "explanation": True,
            "completion": True,
            "pii_detection": settings.enable_pii_detection,
            "learning": settings.enable_learning
        },
        "providers": {
            "current": settings.default_provider,
            "available": ["openai", "anthropic"]
        }
    }