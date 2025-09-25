import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from ..models.factory import ModelFactory
from ..services.pii_detector import PIIDetector
from ..services.learning_service import LearningService
from ..core.config import settings

app = typer.Typer(help="l0l1 - SQL Analysis and Validation Library")
console = Console()


@app.command()
def validate(
    query: str = typer.Argument(..., help="SQL query to validate"),
    schema_file: Optional[Path] = typer.Option(None, "--schema", "-s", help="Schema file for context"),
    workspace: str = typer.Option("default", "--workspace", "-w", help="Workspace name"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="AI provider (openai, anthropic)"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format")
):
    """Validate a SQL query."""
    asyncio.run(_validate_async(query, schema_file, workspace, provider, json_output))


@app.command()
def explain(
    query: str = typer.Argument(..., help="SQL query to explain"),
    schema_file: Optional[Path] = typer.Option(None, "--schema", "-s", help="Schema file for context"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="AI provider (openai, anthropic)")
):
    """Explain a SQL query."""
    asyncio.run(_explain_async(query, schema_file, provider))


@app.command()
def complete(
    partial_query: str = typer.Argument(..., help="Partial SQL query to complete"),
    schema_file: Optional[Path] = typer.Option(None, "--schema", "-s", help="Schema file for context"),
    workspace: str = typer.Option("default", "--workspace", "-w", help="Workspace name"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="AI provider (openai, anthropic)")
):
    """Complete a partial SQL query."""
    asyncio.run(_complete_async(partial_query, schema_file, workspace, provider))


@app.command()
def correct(
    query: str = typer.Argument(..., help="SQL query to correct"),
    error: Optional[str] = typer.Option(None, "--error", "-e", help="Error message"),
    schema_file: Optional[Path] = typer.Option(None, "--schema", "-s", help="Schema file for context"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="AI provider (openai, anthropic)")
):
    """Correct a SQL query."""
    asyncio.run(_correct_async(query, error, schema_file, provider))


@app.command()
def check_pii(
    query: str = typer.Argument(..., help="SQL query to check for PII"),
    anonymize: bool = typer.Option(False, "--anonymize", help="Show anonymized version")
):
    """Check SQL query for personally identifiable information (PII)."""
    detector = PIIDetector()
    pii_findings = detector.detect_pii(query)

    if not pii_findings:
        rprint("[green]✓ No PII detected in the query[/green]")
        return

    rprint(f"[yellow]⚠ Found {len(pii_findings)} PII entities:[/yellow]")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Entity Type")
    table.add_column("Text")
    table.add_column("Position")
    table.add_column("Confidence")

    for finding in pii_findings:
        table.add_row(
            finding["entity_type"],
            finding["text"],
            f"{finding['start']}-{finding['end']}",
            f"{finding['confidence']:.2f}"
        )

    console.print(table)

    if anonymize:
        anonymized_query, _ = detector.anonymize_sql(query)
        rprint("\n[blue]Anonymized query:[/blue]")
        syntax = Syntax(anonymized_query, "sql", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title="Anonymized SQL"))


@app.command()
def learning_stats(
    workspace: str = typer.Option("default", "--workspace", "-w", help="Workspace name")
):
    """Show learning statistics for a workspace."""
    learning_service = LearningService()
    stats = learning_service.get_learning_stats(workspace)

    table = Table(title=f"Learning Statistics - Workspace: {workspace}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Learned Queries", str(stats["total_queries"]))
    table.add_row("Average Execution Time", f"{stats['avg_execution_time']:.3f}s")
    table.add_row("Recent Activity (7 days)", str(stats["recent_activity"]))

    if stats["most_successful"]:
        table.add_row("Most Successful Query", stats["most_successful"]["query"])
        table.add_row("Success Count", str(stats["most_successful"]["success_count"]))

    console.print(table)


@app.command()
def config_show():
    """Show current configuration."""
    table = Table(title="l0l1 Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("AI Provider", settings.default_provider)
    table.add_row("Completion Model", settings.completion_model)
    table.add_row("Embedding Model", settings.embedding_model)
    table.add_row("Database URL", settings.database_url)
    table.add_row("Workspace Directory", settings.workspace_data_dir)
    table.add_row("PII Detection Enabled", str(settings.enable_pii_detection))
    table.add_row("Learning Enabled", str(settings.enable_learning))
    table.add_row("Learning Threshold", str(settings.learning_threshold))

    console.print(table)


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", help="Host to serve on"),
    port: int = typer.Option(8000, "--port", help="Port to serve on"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload")
):
    """Start the FastAPI server."""
    try:
        import uvicorn
        uvicorn.run(
            "l0l1.api.main:app",
            host=host,
            port=port,
            reload=reload
        )
    except ImportError:
        rprint("[red]Error: uvicorn is required to run the server[/red]")
        sys.exit(1)


# Async helper functions
async def _validate_async(query: str, schema_file: Optional[Path], workspace: str, provider: Optional[str], json_output: bool):
    try:
        model = ModelFactory.create_model(provider) if provider else ModelFactory.get_default_model()
        schema_context = _load_schema_file(schema_file) if schema_file else None

        result = await model.validate_sql_query(query, schema_context)

        if json_output:
            import json
            print(json.dumps(result, indent=2))
        else:
            _display_validation_result(query, result)

    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        sys.exit(1)


async def _explain_async(query: str, schema_file: Optional[Path], provider: Optional[str]):
    try:
        model = ModelFactory.create_model(provider) if provider else ModelFactory.get_default_model()
        schema_context = _load_schema_file(schema_file) if schema_file else None

        explanation = await model.explain_sql_query(query, schema_context)

        rprint("[blue]Query Explanation:[/blue]")
        syntax = Syntax(query, "sql", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title="SQL Query"))
        console.print(Panel(explanation, title="Explanation", border_style="blue"))

    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        sys.exit(1)


async def _complete_async(partial_query: str, schema_file: Optional[Path], workspace: str, provider: Optional[str]):
    try:
        model = ModelFactory.create_model(provider) if provider else ModelFactory.get_default_model()
        schema_context = _load_schema_file(schema_file) if schema_file else None

        # Try learning service first
        learning_service = LearningService()
        suggestions = await learning_service.get_query_suggestions(partial_query, workspace, schema_context)

        if suggestions:
            rprint("[green]Query Suggestions (including learned patterns):[/green]")
            for i, suggestion in enumerate(suggestions, 1):
                syntax = Syntax(suggestion, "sql", theme="monokai", line_numbers=True)
                console.print(Panel(syntax, title=f"Suggestion {i}"))
        else:
            # Fallback to AI completion
            completed = await model.complete_sql_query(partial_query, schema_context)
            rprint("[blue]Completed Query:[/blue]")
            syntax = Syntax(completed, "sql", theme="monokai", line_numbers=True)
            console.print(Panel(syntax, title="Completed SQL"))

    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        sys.exit(1)


async def _correct_async(query: str, error: Optional[str], schema_file: Optional[Path], provider: Optional[str]):
    try:
        model = ModelFactory.create_model(provider) if provider else ModelFactory.get_default_model()
        schema_context = _load_schema_file(schema_file) if schema_file else None

        corrected = await model.correct_sql_query(query, error, schema_context)

        rprint("[red]Original Query:[/red]")
        syntax = Syntax(query, "sql", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title="Original SQL"))

        rprint("[green]Corrected Query:[/green]")
        syntax = Syntax(corrected, "sql", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title="Corrected SQL"))

    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        sys.exit(1)


def _load_schema_file(schema_file: Path) -> str:
    """Load schema from file."""
    try:
        return schema_file.read_text()
    except Exception as e:
        rprint(f"[red]Error loading schema file: {e}[/red]")
        sys.exit(1)


def _display_validation_result(query: str, result: dict):
    """Display validation result in a formatted way."""
    syntax = Syntax(query, "sql", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title="SQL Query"))

    if result.get("is_valid", False):
        rprint("[green]✓ Query is valid[/green]")
    else:
        rprint("[red]✗ Query has issues[/red]")

        if result.get("issues"):
            rprint("\n[red]Issues found:[/red]")
            for issue in result["issues"]:
                rprint(f"  • {issue}")

        if result.get("suggestions"):
            rprint("\n[blue]Suggestions:[/blue]")
            for suggestion in result["suggestions"]:
                rprint(f"  • {suggestion}")

        severity = result.get("severity", "medium")
        color = {"low": "yellow", "medium": "orange", "high": "red"}.get(severity, "orange")
        rprint(f"\n[{color}]Severity: {severity.upper()}[/{color}]")


def main():
    """Main CLI entry point."""
    app()


if __name__ == "__main__":
    main()