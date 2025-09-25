import asyncio
from typing import Optional
import ipywidgets as widgets
from IPython.display import display, HTML

from ...models.factory import ModelFactory
from ...services.pii_detector import PIIDetector
from ...services.learning_service import LearningService


class SQLValidatorWidget:
    """Interactive widget for SQL validation in Jupyter notebooks."""

    def __init__(self, workspace: str = "jupyter_widget"):
        self.workspace = workspace
        self.pii_detector = PIIDetector()
        self.learning_service = LearningService()
        self.create_widget()

    def create_widget(self):
        """Create the interactive widget."""
        # SQL input
        self.sql_textarea = widgets.Textarea(
            value='',
            placeholder='Enter your SQL query here...',
            description='SQL Query:',
            layout=widgets.Layout(width='100%', height='150px')
        )

        # Options
        self.validate_checkbox = widgets.Checkbox(
            value=True,
            description='Validate Query',
            indent=False
        )

        self.explain_checkbox = widgets.Checkbox(
            value=False,
            description='Explain Query',
            indent=False
        )

        self.pii_checkbox = widgets.Checkbox(
            value=True,
            description='Check PII',
            indent=False
        )

        self.complete_checkbox = widgets.Checkbox(
            value=False,
            description='Get Suggestions',
            indent=False
        )

        # Provider selection
        self.provider_dropdown = widgets.Dropdown(
            options=['openai', 'anthropic'],
            value='openai',
            description='AI Provider:'
        )

        # Schema input
        self.schema_textarea = widgets.Textarea(
            value='',
            placeholder='Optional: Enter schema context...',
            description='Schema:',
            layout=widgets.Layout(width='100%', height='100px')
        )

        # Analyze button
        self.analyze_button = widgets.Button(
            description='🔍 Analyze SQL',
            button_style='primary',
            layout=widgets.Layout(width='200px')
        )

        # Results area
        self.results_output = widgets.Output()

        # Layout
        options_row = widgets.HBox([
            self.validate_checkbox,
            self.explain_checkbox,
            self.pii_checkbox,
            self.complete_checkbox
        ])

        config_row = widgets.HBox([self.provider_dropdown])

        self.widget = widgets.VBox([
            widgets.HTML("<h3>🚀 l0l1 SQL Validator</h3>"),
            self.sql_textarea,
            widgets.HTML("<h4>Options</h4>"),
            options_row,
            config_row,
            widgets.HTML("<h4>Schema Context (Optional)</h4>"),
            self.schema_textarea,
            self.analyze_button,
            self.results_output
        ])

        # Event handler
        self.analyze_button.on_click(self._on_analyze_click)

    def _on_analyze_click(self, button):
        """Handle analyze button click."""
        self.results_output.clear_output()

        with self.results_output:
            query = self.sql_textarea.value.strip()
            if not query:
                display(HTML('<div style="color: red;">Please enter a SQL query</div>'))
                return

            # Run async analysis
            loop = asyncio.get_event_loop()
            if loop.is_running():
                try:
                    import nest_asyncio
                    nest_asyncio.apply()
                except ImportError:
                    display(HTML('<div style="color: red;">Error: nest_asyncio is required</div>'))
                    return

            asyncio.run(self._analyze_query(query))

    async def _analyze_query(self, query: str):
        """Analyze the SQL query."""
        schema_context = self.schema_textarea.value.strip() or None
        model = ModelFactory.create_model(self.provider_dropdown.value)

        results_html = """
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #dee2e6; margin-top: 10px;">
            <h4 style="color: #007bff; margin-top: 0;">📊 Analysis Results</h4>
        """

        # Display query
        results_html += f"""
        <div style="margin: 15px 0;">
            <strong>Query:</strong>
            <div style="background: #2d3748; color: #e2e8f0; padding: 15px; border-radius: 5px; font-family: 'Monaco', 'Consolas', monospace; white-space: pre-wrap; overflow-x: auto; margin-top: 5px;">
{query}
            </div>
        </div>
        """

        # PII Check
        if self.pii_checkbox.value:
            pii_findings = self.pii_detector.detect_pii(query)
            if pii_findings:
                results_html += """
                <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 15px 0;">
                    <h5 style="color: #856404; margin-top: 0;">⚠️ PII Detected</h5>
                """
                for finding in pii_findings:
                    results_html += f"<div>• <strong>{finding['entity_type']}:</strong> <code>{finding['text']}</code> (confidence: {finding['confidence']:.2f})</div>"
                results_html += "</div>"
            else:
                results_html += """
                <div style="background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 15px 0;">
                    <div style="color: #155724;">✅ No PII detected</div>
                </div>
                """

        # Validation
        if self.validate_checkbox.value:
            try:
                validation_result = await model.validate_sql_query(query, schema_context)
                if validation_result.get("is_valid", False):
                    results_html += """
                    <div style="background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 15px 0;">
                        <div style="color: #155724;">✅ Query is valid</div>
                    </div>
                    """
                else:
                    results_html += f"""
                    <div style="background: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 15px 0;">
                        <h5 style="color: #721c24; margin-top: 0;">❌ Validation Issues ({validation_result.get('severity', 'medium')} severity)</h5>
                    """
                    for issue in validation_result.get("issues", []):
                        results_html += f"<div>• {issue}</div>"

                    if validation_result.get("suggestions"):
                        results_html += "<br><strong>Suggestions:</strong>"
                        for suggestion in validation_result["suggestions"]:
                            results_html += f"<div>• {suggestion}</div>"
                    results_html += "</div>"
            except Exception as e:
                results_html += f'<div style="background: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 15px 0;"><strong>Validation Error:</strong> {str(e)}</div>'

        # Explanation
        if self.explain_checkbox.value:
            try:
                explanation = await model.explain_sql_query(query, schema_context)
                results_html += f"""
                <div style="background: #e3f2fd; border-left: 4px solid #2196f3; padding: 15px; margin: 15px 0;">
                    <h5 style="color: #0d47a1; margin-top: 0;">📝 Query Explanation</h5>
                    <div>{explanation.replace(chr(10), '<br>')}</div>
                </div>
                """
            except Exception as e:
                results_html += f'<div style="background: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 15px 0;"><strong>Explanation Error:</strong> {str(e)}</div>'

        # Suggestions
        if self.complete_checkbox.value:
            try:
                suggestions = await self.learning_service.get_query_suggestions(
                    query, self.workspace, schema_context
                )
                if suggestions:
                    results_html += """
                    <div style="background: #e8f5e8; border-left: 4px solid #4caf50; padding: 15px; margin: 15px 0;">
                        <h5 style="color: #2e7d32; margin-top: 0;">💡 Query Suggestions</h5>
                    """
                    for i, suggestion in enumerate(suggestions[:3], 1):  # Limit to top 3
                        results_html += f"""
                        <div style="margin: 10px 0;">
                            <strong>Option {i}:</strong>
                            <div style="background: #2d3748; color: #e2e8f0; padding: 10px; border-radius: 5px; font-family: 'Monaco', 'Consolas', monospace; white-space: pre-wrap; overflow-x: auto; margin-top: 5px; font-size: 0.9em;">
{suggestion}
                            </div>
                        </div>
                        """
                    results_html += "</div>"
            except Exception as e:
                results_html += f'<div style="background: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 15px 0;"><strong>Suggestions Error:</strong> {str(e)}</div>'

        results_html += "</div>"
        display(HTML(results_html))

    def display(self):
        """Display the widget."""
        display(self.widget)


def create_sql_validator(workspace: str = "jupyter_widget") -> SQLValidatorWidget:
    """Create and return a SQL validator widget."""
    widget = SQLValidatorWidget(workspace)
    return widget