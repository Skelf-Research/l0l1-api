import asyncio
from typing import Optional
from IPython.core.magic import Magics, line_magic, cell_magic, magics_class
from IPython.core.display import HTML, display, Markdown
from IPython.core.magic_arguments import (argument, magic_arguments, parse_argstring)
import json

from ...models.factory import ModelFactory
from ...services.pii_detector import PIIDetector
from ...services.learning_service import LearningService
from ...core.config import settings


@magics_class
class L0L1Magic(Magics):
    """IPython magic commands for l0l1 SQL analysis."""

    def __init__(self, shell=None):
        super().__init__(shell)
        self.pii_detector = PIIDetector()
        self.learning_service = LearningService()
        self.current_workspace = "jupyter_default"

    @line_magic
    @magic_arguments()
    @argument('--workspace', '-w', help='Set workspace name')
    @argument('--provider', '-p', help='AI provider (openai, anthropic)')
    @argument('--model', '-m', help='Model name')
    def l0l1_config(self, line):
        """Configure l0l1 settings for the current session."""
        args = parse_argstring(self.l0l1_config, line)

        config_html = """
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #007bff;">
            <h4 style="margin-top: 0; color: #007bff;">🔧 l0l1 Configuration</h4>
            <table style="width: 100%; border-collapse: collapse;">
        """

        if args.workspace:
            self.current_workspace = args.workspace
            config_html += f"<tr><td><strong>Workspace:</strong></td><td>{self.current_workspace}</td></tr>"

        if args.provider:
            settings.default_provider = args.provider
            ModelFactory.reset_default_model()
            config_html += f"<tr><td><strong>AI Provider:</strong></td><td>{args.provider}</td></tr>"

        if args.model:
            settings.completion_model = args.model
            ModelFactory.reset_default_model()
            config_html += f"<tr><td><strong>Model:</strong></td><td>{args.model}</td></tr>"

        # Show current configuration
        config_html += f"""
            <tr><td><strong>Current Workspace:</strong></td><td>{self.current_workspace}</td></tr>
            <tr><td><strong>Current Provider:</strong></td><td>{settings.default_provider}</td></tr>
            <tr><td><strong>Current Model:</strong></td><td>{settings.completion_model}</td></tr>
            <tr><td><strong>PII Detection:</strong></td><td>{'Enabled' if settings.enable_pii_detection else 'Disabled'}</td></tr>
            <tr><td><strong>Learning:</strong></td><td>{'Enabled' if settings.enable_learning else 'Disabled'}</td></tr>
        """

        config_html += "</table></div>"
        display(HTML(config_html))

    @cell_magic
    @magic_arguments()
    @argument('--validate', action='store_true', help='Validate the SQL query')
    @argument('--explain', action='store_true', help='Explain the SQL query')
    @argument('--check-pii', action='store_true', help='Check for PII in the query')
    @argument('--complete', action='store_true', help='Complete partial SQL query')
    @argument('--schema', help='Schema context for the query')
    @argument('--anonymize', action='store_true', help='Show anonymized version (with --check-pii)')
    def l0l1_sql(self, line, cell):
        """Analyze SQL query with l0l1."""
        args = parse_argstring(self.l0l1_sql, line)
        query = cell.strip()

        # Run async operations
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an event loop, use nest_asyncio
            try:
                import nest_asyncio
                nest_asyncio.apply()
            except ImportError:
                display(HTML('<div style="color: red;">Error: nest_asyncio is required for Jupyter integration</div>'))
                return

        return asyncio.run(self._analyze_sql(query, args))

    async def _analyze_sql(self, query: str, args):
        """Analyze SQL query based on arguments."""
        model = ModelFactory.get_default_model()

        results_html = """
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 10px 0;">
            <h3 style="margin-top: 0; color: #28a745;">📊 SQL Analysis Results</h3>
        """

        # Display the query
        results_html += f"""
        <div style="background: #2d3748; color: #e2e8f0; padding: 15px; border-radius: 5px; margin: 10px 0; font-family: 'Consolas', 'Monaco', monospace; white-space: pre-wrap; overflow-x: auto;">
{query}
        </div>
        """

        # PII Check
        if args.check_pii or settings.enable_pii_detection:
            pii_findings = self.pii_detector.detect_pii(query)
            if pii_findings:
                results_html += """
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 5px; margin: 10px 0;">
                    <strong>⚠️ PII Detected:</strong><br>
                """
                for finding in pii_findings:
                    results_html += f"• {finding['entity_type']}: <code>{finding['text']}</code> (confidence: {finding['confidence']:.2f})<br>"

                if args.anonymize:
                    anonymized_query, _ = self.pii_detector.anonymize_sql(query)
                    results_html += f"""
                    <div style="margin-top: 10px;">
                        <strong>Anonymized Query:</strong>
                        <div style="background: #2d3748; color: #e2e8f0; padding: 10px; border-radius: 5px; font-family: 'Consolas', 'Monaco', monospace; white-space: pre-wrap; overflow-x: auto; margin-top: 5px;">
{anonymized_query}
                        </div>
                    </div>
                    """
                results_html += "</div>"
            else:
                results_html += """
                <div style="background: #d4edda; border: 1px solid #c3e6cb; padding: 10px; border-radius: 5px; margin: 10px 0;">
                    <strong>✅ No PII detected</strong>
                </div>
                """

        # Validation
        if args.validate:
            try:
                validation_result = await model.validate_sql_query(query, args.schema)
                if validation_result.get("is_valid", False):
                    results_html += """
                    <div style="background: #d4edda; border: 1px solid #c3e6cb; padding: 10px; border-radius: 5px; margin: 10px 0;">
                        <strong>✅ Query is valid</strong>
                    </div>
                    """
                else:
                    results_html += f"""
                    <div style="background: #f8d7da; border: 1px solid #f5c6cb; padding: 10px; border-radius: 5px; margin: 10px 0;">
                        <strong>❌ Query validation issues ({validation_result.get('severity', 'medium')} severity):</strong><br>
                    """
                    for issue in validation_result.get("issues", []):
                        results_html += f"• {issue}<br>"

                    if validation_result.get("suggestions"):
                        results_html += "<br><strong>Suggestions:</strong><br>"
                        for suggestion in validation_result["suggestions"]:
                            results_html += f"• {suggestion}<br>"
                    results_html += "</div>"
            except Exception as e:
                results_html += f'<div style="background: #f8d7da; padding: 10px; border-radius: 5px; margin: 10px 0;"><strong>Error validating query:</strong> {str(e)}</div>'

        # Explanation
        if args.explain:
            try:
                explanation = await model.explain_sql_query(query, args.schema)
                results_html += f"""
                <div style="background: #e3f2fd; border: 1px solid #90caf9; padding: 15px; border-radius: 5px; margin: 10px 0;">
                    <strong>📝 Query Explanation:</strong><br><br>
                    {explanation.replace('\n', '<br>')}
                </div>
                """
            except Exception as e:
                results_html += f'<div style="background: #f8d7da; padding: 10px; border-radius: 5px; margin: 10px 0;"><strong>Error explaining query:</strong> {str(e)}</div>'

        # Completion suggestions
        if args.complete:
            try:
                suggestions = await self.learning_service.get_query_suggestions(
                    query, self.current_workspace, args.schema
                )
                if suggestions:
                    results_html += """
                    <div style="background: #e8f5e8; border: 1px solid #4caf50; padding: 15px; border-radius: 5px; margin: 10px 0;">
                        <strong>💡 Query Suggestions:</strong><br><br>
                    """
                    for i, suggestion in enumerate(suggestions, 1):
                        results_html += f"""
                        <div style="margin: 10px 0;">
                            <strong>Option {i}:</strong>
                            <div style="background: #2d3748; color: #e2e8f0; padding: 10px; border-radius: 5px; font-family: 'Consolas', 'Monaco', monospace; white-space: pre-wrap; overflow-x: auto; margin-top: 5px;">
{suggestion}
                            </div>
                        </div>
                        """
                    results_html += "</div>"
            except Exception as e:
                results_html += f'<div style="background: #f8d7da; padding: 10px; border-radius: 5px; margin: 10px 0;"><strong>Error getting suggestions:</strong> {str(e)}</div>'

        # Learning stats
        learning_stats = self.learning_service.get_learning_stats(self.current_workspace)
        if learning_stats["total_queries"] > 0:
            results_html += f"""
            <div style="background: #f3e5f5; border: 1px solid #ce93d8; padding: 10px; border-radius: 5px; margin: 10px 0; font-size: 0.9em;">
                <strong>🧠 Learning Stats:</strong>
                {learning_stats["total_queries"]} learned queries |
                Avg execution: {learning_stats["avg_execution_time"]:.3f}s |
                Recent activity: {learning_stats["recent_activity"]}
            </div>
            """

        results_html += "</div>"
        display(HTML(results_html))

    @line_magic
    def l0l1_status(self, line):
        """Show current l0l1 status and statistics."""
        stats = self.learning_service.get_learning_stats(self.current_workspace)

        status_html = f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin: 10px 0;">
            <h3 style="margin-top: 0;">🚀 l0l1 Status Dashboard</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px;">
                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px;">
                    <h4 style="margin: 0 0 10px 0;">Workspace</h4>
                    <p style="margin: 0; font-size: 1.2em;">{self.current_workspace}</p>
                </div>
                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px;">
                    <h4 style="margin: 0 0 10px 0;">AI Provider</h4>
                    <p style="margin: 0; font-size: 1.2em;">{settings.default_provider}</p>
                </div>
                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px;">
                    <h4 style="margin: 0 0 10px 0;">Learned Queries</h4>
                    <p style="margin: 0; font-size: 1.2em;">{stats["total_queries"]}</p>
                </div>
                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px;">
                    <h4 style="margin: 0 0 10px 0;">PII Detection</h4>
                    <p style="margin: 0; font-size: 1.2em;">{'✅ Enabled' if settings.enable_pii_detection else '❌ Disabled'}</p>
                </div>
            </div>
        </div>
        """

        display(HTML(status_html))


def load_ipython_extension(ipython):
    """Load the l0l1 IPython extension."""
    ipython.register_magic_function(L0L1Magic)

    # Display welcome message
    welcome_html = """
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin: 20px 0;">
        <h2 style="margin-top: 0;">🎉 l0l1 Jupyter Extension Loaded!</h2>
        <p>Use the following magic commands:</p>
        <ul>
            <li><code>%l0l1_config --workspace myproject --provider openai</code> - Configure settings</li>
            <li><code>%%l0l1_sql --validate --explain</code> - Analyze SQL in cell</li>
            <li><code>%l0l1_status</code> - Show status dashboard</li>
        </ul>
        <p><strong>Cell magic options:</strong></p>
        <ul>
            <li><code>--validate</code> - Check query validity</li>
            <li><code>--explain</code> - Get query explanation</li>
            <li><code>--check-pii</code> - Detect personally identifiable information</li>
            <li><code>--complete</code> - Get completion suggestions</li>
            <li><code>--anonymize</code> - Show anonymized version (with --check-pii)</li>
        </ul>
    </div>
    """

    display(HTML(welcome_html))