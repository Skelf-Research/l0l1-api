"""IPython magic commands for l0l1 SQL analysis."""

import asyncio
from typing import Optional
from IPython.core.magic import Magics, line_magic, cell_magic, magics_class
from IPython.display import HTML, display
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring

from .client import L0l1JupyterClient
from ...core.config import settings


@magics_class
class L0L1Magic(Magics):
    """IPython magic commands for l0l1 SQL analysis."""

    def __init__(self, shell):
        super().__init__(shell)
        self.client = L0l1JupyterClient()
        self.current_workspace = "jupyter_default"
        self.schema_context: Optional[str] = None

    def _run_async(self, coro):
        """Run async coroutine in Jupyter environment."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # We're in a running event loop (e.g., Jupyter)
            try:
                import nest_asyncio
                nest_asyncio.apply()
                return asyncio.get_event_loop().run_until_complete(coro)
            except ImportError:
                display(HTML(
                    '<div style="background:#f8d7da;padding:10px;border-radius:5px;color:#721c24;">'
                    '<strong>Error:</strong> nest_asyncio is required. Install with: '
                    '<code>pip install nest_asyncio</code></div>'
                ))
                return None
        else:
            return asyncio.run(coro)

    @line_magic
    @magic_arguments()
    @argument('--workspace', '-w', help='Set workspace name')
    @argument('--provider', '-p', choices=['openai', 'anthropic'], help='AI provider')
    @argument('--api-url', help='l0l1 API server URL')
    @argument('--schema', '-s', help='Path to schema file')
    def l0l1_config(self, line):
        """Configure l0l1 settings for the current session.

        Examples:
            %l0l1_config --workspace myproject
            %l0l1_config --provider anthropic
            %l0l1_config --api-url http://localhost:8000
            %l0l1_config --schema ./schema.sql
        """
        args = parse_argstring(self.l0l1_config, line)

        changes = []

        if args.workspace:
            self.current_workspace = args.workspace
            changes.append(('Workspace', self.current_workspace))

        if args.provider:
            self.client.set_provider(args.provider)
            changes.append(('AI Provider', args.provider))

        if args.api_url:
            self.client.set_api_url(args.api_url)
            changes.append(('API URL', args.api_url))

        if args.schema:
            try:
                with open(args.schema, 'r') as f:
                    self.schema_context = f.read()
                changes.append(('Schema', f'Loaded from {args.schema}'))
            except Exception as e:
                display(HTML(f'<div style="color:red;">Error loading schema: {e}</div>'))
                return

        # Display configuration
        html = self._render_config_panel(changes)
        display(HTML(html))

    @line_magic
    def l0l1_status(self, line):
        """Show current l0l1 status and statistics.

        Example:
            %l0l1_status
        """
        status = self._run_async(self.client.get_status())

        html = f'''
        <div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:20px;border-radius:10px;margin:10px 0;">
            <h3 style="margin-top:0;">l0l1 Status Dashboard</h3>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:15px;margin-top:15px;">
                <div style="background:rgba(255,255,255,0.15);padding:15px;border-radius:8px;">
                    <div style="font-size:0.85em;opacity:0.9;">Workspace</div>
                    <div style="font-size:1.3em;font-weight:bold;">{self.current_workspace}</div>
                </div>
                <div style="background:rgba(255,255,255,0.15);padding:15px;border-radius:8px;">
                    <div style="font-size:0.85em;opacity:0.9;">Server Status</div>
                    <div style="font-size:1.3em;font-weight:bold;">{"Connected" if status.get("connected") else "Disconnected"}</div>
                </div>
                <div style="background:rgba(255,255,255,0.15);padding:15px;border-radius:8px;">
                    <div style="font-size:0.85em;opacity:0.9;">AI Provider</div>
                    <div style="font-size:1.3em;font-weight:bold;">{status.get("provider", "N/A")}</div>
                </div>
                <div style="background:rgba(255,255,255,0.15);padding:15px;border-radius:8px;">
                    <div style="font-size:0.85em;opacity:0.9;">Schema Loaded</div>
                    <div style="font-size:1.3em;font-weight:bold;">{"Yes" if self.schema_context else "No"}</div>
                </div>
            </div>
        </div>
        '''
        display(HTML(html))

    @line_magic
    def l0l1_schema(self, line):
        """Set schema context from a file or clear it.

        Examples:
            %l0l1_schema ./schema.sql    # Load schema from file
            %l0l1_schema --clear         # Clear schema context
        """
        line = line.strip()

        if line == '--clear' or line == '-c':
            self.schema_context = None
            display(HTML('<div style="color:#28a745;">Schema context cleared</div>'))
            return

        if not line:
            if self.schema_context:
                display(HTML(f'''
                <div style="background:#e3f2fd;padding:15px;border-radius:8px;border-left:4px solid #2196f3;">
                    <strong>Current Schema:</strong>
                    <pre style="background:#1e1e1e;color:#d4d4d4;padding:10px;border-radius:4px;margin-top:10px;overflow-x:auto;">{self.schema_context[:500]}{"..." if len(self.schema_context) > 500 else ""}</pre>
                </div>
                '''))
            else:
                display(HTML('<div style="color:#6c757d;">No schema context set</div>'))
            return

        try:
            with open(line, 'r') as f:
                self.schema_context = f.read()
            display(HTML(f'<div style="color:#28a745;">Schema loaded from {line}</div>'))
        except Exception as e:
            display(HTML(f'<div style="color:#dc3545;">Error loading schema: {e}</div>'))

    @cell_magic
    @magic_arguments()
    @argument('--validate', '-v', action='store_true', help='Validate the SQL query')
    @argument('--explain', '-e', action='store_true', help='Explain the SQL query')
    @argument('--check-pii', '-p', action='store_true', help='Check for PII')
    @argument('--anonymize', '-a', action='store_true', help='Show anonymized version')
    @argument('--complete', '-c', action='store_true', help='Get completion suggestions')
    @argument('--execute', '-x', action='store_true', help='Execute after validation (requires connection)')
    @argument('--schema', '-s', help='Inline schema context')
    def l0l1_sql(self, line, cell):
        """Analyze SQL query with l0l1.

        Examples:
            %%l0l1_sql --validate --explain
            SELECT * FROM users WHERE id = 1

            %%l0l1_sql --check-pii --anonymize
            SELECT email FROM users WHERE ssn = '123-45-6789'

            %%l0l1_sql --complete
            SELECT name FROM users WHERE
        """
        args = parse_argstring(self.l0l1_sql, line)
        query = cell.strip()

        if not query:
            display(HTML('<div style="color:#dc3545;">No SQL query provided</div>'))
            return

        # Use inline schema or stored schema
        schema = args.schema or self.schema_context

        # Default to validate if no options specified
        if not any([args.validate, args.explain, args.check_pii, args.complete]):
            args.validate = True

        result = self._run_async(self._analyze_sql(query, args, schema))
        return result

    async def _analyze_sql(self, query: str, args, schema: Optional[str]):
        """Analyze SQL query based on arguments."""
        sections = []

        # Query display
        sections.append(self._render_query_section(query))

        # PII Check
        if args.check_pii:
            pii_result = await self.client.check_pii(query)
            sections.append(self._render_pii_section(pii_result, args.anonymize))

        # Validation
        if args.validate:
            validation_result = await self.client.validate(
                query, self.current_workspace, schema
            )
            sections.append(self._render_validation_section(validation_result))

        # Explanation
        if args.explain:
            explanation = await self.client.explain(query, self.current_workspace)
            sections.append(self._render_explanation_section(explanation))

        # Completions
        if args.complete:
            completions = await self.client.complete(query, self.current_workspace)
            sections.append(self._render_completions_section(completions))

        # Render full output
        html = f'''
        <div style="background:#f8f9fa;padding:20px;border-radius:10px;margin:10px 0;border:1px solid #dee2e6;">
            <h3 style="margin-top:0;color:#495057;">SQL Analysis Results</h3>
            {''.join(sections)}
        </div>
        '''
        display(HTML(html))

    def _render_config_panel(self, changes):
        """Render configuration panel HTML."""
        rows = ''.join([
            f'<tr><td style="padding:5px 10px;"><strong>{k}:</strong></td><td style="padding:5px 10px;">{v}</td></tr>'
            for k, v in changes
        ]) if changes else '<tr><td>No changes made</td></tr>'

        return f'''
        <div style="background:#e3f2fd;padding:15px;border-radius:8px;border-left:4px solid #2196f3;">
            <h4 style="margin-top:0;color:#1565c0;">l0l1 Configuration Updated</h4>
            <table style="width:100%;">{rows}</table>
        </div>
        '''

    def _render_query_section(self, query: str):
        """Render the SQL query section."""
        escaped = query.replace('<', '&lt;').replace('>', '&gt;')
        return f'''
        <div style="margin-bottom:15px;">
            <div style="font-weight:bold;margin-bottom:5px;color:#6c757d;">Query</div>
            <pre style="background:#1e1e1e;color:#d4d4d4;padding:15px;border-radius:6px;margin:0;overflow-x:auto;font-family:'Fira Code','Monaco','Consolas',monospace;">{escaped}</pre>
        </div>
        '''

    def _render_pii_section(self, result: dict, show_anonymized: bool):
        """Render PII detection section."""
        if not result.get('has_pii'):
            return '''
            <div style="background:#d4edda;border-left:4px solid #28a745;padding:12px;margin:10px 0;border-radius:0 6px 6px 0;">
                <span style="color:#155724;">No PII detected</span>
            </div>
            '''

        detections = result.get('detections', [])
        items = ''.join([
            f'<div style="margin:5px 0;"><code style="background:#fff3cd;padding:2px 6px;border-radius:3px;">{d.get("entity_type")}</code>: {d.get("value")} <span style="color:#6c757d;">(confidence: {d.get("score", 0):.0%})</span></div>'
            for d in detections
        ])

        anonymized_html = ''
        if show_anonymized and result.get('anonymized_query'):
            escaped = result['anonymized_query'].replace('<', '&lt;').replace('>', '&gt;')
            anonymized_html = f'''
            <div style="margin-top:10px;">
                <div style="font-weight:bold;color:#856404;">Anonymized Query:</div>
                <pre style="background:#1e1e1e;color:#d4d4d4;padding:10px;border-radius:4px;margin-top:5px;font-size:0.9em;">{escaped}</pre>
            </div>
            '''

        return f'''
        <div style="background:#fff3cd;border-left:4px solid #ffc107;padding:12px;margin:10px 0;border-radius:0 6px 6px 0;">
            <div style="font-weight:bold;color:#856404;margin-bottom:8px;">PII Detected</div>
            {items}
            {anonymized_html}
        </div>
        '''

    def _render_validation_section(self, result: dict):
        """Render validation results section."""
        if result.get('valid', True) and not result.get('errors') and not result.get('warnings'):
            return '''
            <div style="background:#d4edda;border-left:4px solid #28a745;padding:12px;margin:10px 0;border-radius:0 6px 6px 0;">
                <span style="color:#155724;">Query is valid</span>
            </div>
            '''

        errors = result.get('errors', [])
        warnings = result.get('warnings', [])
        suggestions = result.get('suggestions', [])

        error_items = ''.join([f'<div style="color:#721c24;">• {e}</div>' for e in errors])
        warning_items = ''.join([f'<div style="color:#856404;">• {w}</div>' for w in warnings])
        suggestion_items = ''.join([f'<div style="color:#155724;">• {s}</div>' for s in suggestions])

        bg_color = '#f8d7da' if errors else '#fff3cd'
        border_color = '#dc3545' if errors else '#ffc107'
        title = 'Validation Errors' if errors else 'Validation Warnings'

        return f'''
        <div style="background:{bg_color};border-left:4px solid {border_color};padding:12px;margin:10px 0;border-radius:0 6px 6px 0;">
            <div style="font-weight:bold;margin-bottom:8px;">{title}</div>
            {error_items}
            {warning_items}
            {f'<div style="margin-top:10px;"><strong>Suggestions:</strong>{suggestion_items}</div>' if suggestions else ''}
        </div>
        '''

    def _render_explanation_section(self, result: dict):
        """Render explanation section."""
        explanation = result.get('explanation', 'No explanation available')
        complexity = result.get('complexity', 'unknown')
        tables = result.get('tables', [])

        tables_html = ''.join([
            f'<span style="background:#e9ecef;padding:2px 8px;border-radius:4px;margin-right:5px;font-size:0.9em;">{t}</span>'
            for t in tables
        ]) if tables else '<span style="color:#6c757d;">None detected</span>'

        return f'''
        <div style="background:#e3f2fd;border-left:4px solid #2196f3;padding:12px;margin:10px 0;border-radius:0 6px 6px 0;">
            <div style="font-weight:bold;color:#1565c0;margin-bottom:8px;">Query Explanation</div>
            <div style="line-height:1.6;">{explanation}</div>
            <div style="margin-top:12px;display:flex;gap:20px;flex-wrap:wrap;">
                <div><strong>Complexity:</strong> <span style="text-transform:capitalize;">{complexity}</span></div>
                <div><strong>Tables:</strong> {tables_html}</div>
            </div>
        </div>
        '''

    def _render_completions_section(self, result: dict):
        """Render completions section."""
        completions = result.get('completions', [])

        if not completions:
            return '''
            <div style="background:#e8f5e9;border-left:4px solid #4caf50;padding:12px;margin:10px 0;border-radius:0 6px 6px 0;">
                <span style="color:#2e7d32;">No completion suggestions available</span>
            </div>
            '''

        items = ''
        for i, completion in enumerate(completions[:5], 1):
            escaped = completion.replace('<', '&lt;').replace('>', '&gt;')
            items += f'''
            <div style="margin:10px 0;">
                <div style="font-weight:bold;color:#2e7d32;">Option {i}</div>
                <pre style="background:#1e1e1e;color:#d4d4d4;padding:10px;border-radius:4px;margin:5px 0;font-size:0.9em;overflow-x:auto;">{escaped}</pre>
            </div>
            '''

        return f'''
        <div style="background:#e8f5e9;border-left:4px solid #4caf50;padding:12px;margin:10px 0;border-radius:0 6px 6px 0;">
            <div style="font-weight:bold;color:#2e7d32;margin-bottom:8px;">Completion Suggestions</div>
            {items}
        </div>
        '''


def load_ipython_extension(ipython):
    """Load the l0l1 IPython extension."""
    magics = L0L1Magic(ipython)
    ipython.register_magics(magics)

    # Display welcome message
    html = '''
    <div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:20px;border-radius:10px;margin:10px 0;">
        <h2 style="margin-top:0;">l0l1 Jupyter Extension Loaded</h2>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:15px;margin-top:15px;">
            <div>
                <strong>Configuration</strong>
                <div style="font-family:monospace;font-size:0.9em;margin-top:5px;">
                    %l0l1_config --workspace name<br>
                    %l0l1_schema ./schema.sql<br>
                    %l0l1_status
                </div>
            </div>
            <div>
                <strong>SQL Analysis</strong>
                <div style="font-family:monospace;font-size:0.9em;margin-top:5px;">
                    %%l0l1_sql --validate<br>
                    %%l0l1_sql --explain<br>
                    %%l0l1_sql --check-pii
                </div>
            </div>
        </div>
    </div>
    '''
    display(HTML(html))


def unload_ipython_extension(ipython):
    """Unload the l0l1 IPython extension."""
    pass
