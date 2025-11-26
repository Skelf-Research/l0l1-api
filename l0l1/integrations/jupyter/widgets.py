"""Interactive Jupyter widgets for l0l1 SQL analysis."""

import asyncio
from typing import Optional, List, Callable
import ipywidgets as widgets
from IPython.display import display, HTML

from .client import L0l1JupyterClient


class SQLValidatorWidget:
    """Interactive widget for SQL validation in Jupyter notebooks."""

    def __init__(
        self,
        workspace: str = "jupyter_widget",
        api_url: str = "http://localhost:8000"
    ):
        self.workspace = workspace
        self.client = L0l1JupyterClient(api_url=api_url)
        self.schema_context: Optional[str] = None
        self._create_widget()

    def _run_async(self, coro):
        """Run async coroutine."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            try:
                import nest_asyncio
                nest_asyncio.apply()
                return asyncio.get_event_loop().run_until_complete(coro)
            except ImportError:
                return None
        else:
            return asyncio.run(coro)

    def _create_widget(self):
        """Create the interactive widget components."""
        # Header
        self.header = widgets.HTML(
            value='<h3 style="margin:0;color:#667eea;">l0l1 SQL Validator</h3>'
        )

        # SQL input area
        self.sql_input = widgets.Textarea(
            placeholder='Enter your SQL query here...',
            layout=widgets.Layout(width='100%', height='150px'),
            style={'description_width': '0px'}
        )

        # Analysis options
        self.validate_cb = widgets.Checkbox(value=True, description='Validate', indent=False)
        self.explain_cb = widgets.Checkbox(value=False, description='Explain', indent=False)
        self.pii_cb = widgets.Checkbox(value=True, description='Check PII', indent=False)
        self.complete_cb = widgets.Checkbox(value=False, description='Suggestions', indent=False)

        options_box = widgets.HBox(
            [self.validate_cb, self.explain_cb, self.pii_cb, self.complete_cb],
            layout=widgets.Layout(margin='10px 0')
        )

        # Schema input (collapsible)
        self.schema_input = widgets.Textarea(
            placeholder='Optional: Paste your database schema here for context-aware validation...',
            layout=widgets.Layout(width='100%', height='100px'),
            style={'description_width': '0px'}
        )

        self.schema_accordion = widgets.Accordion(
            children=[self.schema_input],
            selected_index=None
        )
        self.schema_accordion.set_title(0, 'Schema Context (Optional)')

        # Analyze button
        self.analyze_btn = widgets.Button(
            description='Analyze SQL',
            button_style='primary',
            icon='search',
            layout=widgets.Layout(width='150px')
        )
        self.analyze_btn.on_click(self._on_analyze)

        # Clear button
        self.clear_btn = widgets.Button(
            description='Clear',
            button_style='',
            icon='trash',
            layout=widgets.Layout(width='100px')
        )
        self.clear_btn.on_click(self._on_clear)

        button_box = widgets.HBox(
            [self.analyze_btn, self.clear_btn],
            layout=widgets.Layout(margin='10px 0')
        )

        # Results output area
        self.results_output = widgets.Output(
            layout=widgets.Layout(border='1px solid #dee2e6', border_radius='5px', padding='10px')
        )

        # Assemble the widget
        self.widget = widgets.VBox([
            self.header,
            widgets.HTML('<label style="color:#6c757d;font-size:0.9em;">SQL Query</label>'),
            self.sql_input,
            widgets.HTML('<label style="color:#6c757d;font-size:0.9em;">Analysis Options</label>'),
            options_box,
            self.schema_accordion,
            button_box,
            self.results_output
        ], layout=widgets.Layout(padding='15px'))

    def _on_analyze(self, btn):
        """Handle analyze button click."""
        self.results_output.clear_output()
        query = self.sql_input.value.strip()

        if not query:
            with self.results_output:
                display(HTML('<div style="color:#dc3545;">Please enter a SQL query</div>'))
            return

        # Get schema context
        schema = self.schema_input.value.strip() or None

        # Run analysis
        self._run_async(self._analyze(query, schema))

    def _on_clear(self, btn):
        """Handle clear button click."""
        self.sql_input.value = ''
        self.results_output.clear_output()

    async def _analyze(self, query: str, schema: Optional[str]):
        """Run the analysis."""
        with self.results_output:
            sections = []

            # Query display
            escaped = query.replace('<', '&lt;').replace('>', '&gt;')
            sections.append(f'''
            <div style="margin-bottom:15px;">
                <pre style="background:#1e1e1e;color:#d4d4d4;padding:12px;border-radius:5px;margin:0;overflow-x:auto;">{escaped}</pre>
            </div>
            ''')

            # PII Check
            if self.pii_cb.value:
                result = await self.client.check_pii(query)
                if result.get('has_pii'):
                    detections = result.get('detections', [])
                    items = ''.join([
                        f'<div>• <code>{d["entity_type"]}</code>: {d["value"]}</div>'
                        for d in detections
                    ])
                    sections.append(f'''
                    <div style="background:#fff3cd;border-left:4px solid #ffc107;padding:10px;margin:10px 0;border-radius:0 5px 5px 0;">
                        <strong style="color:#856404;">PII Detected</strong>
                        {items}
                    </div>
                    ''')
                else:
                    sections.append('''
                    <div style="background:#d4edda;border-left:4px solid #28a745;padding:10px;margin:10px 0;border-radius:0 5px 5px 0;">
                        <span style="color:#155724;">No PII detected</span>
                    </div>
                    ''')

            # Validation
            if self.validate_cb.value:
                result = await self.client.validate(query, self.workspace, schema)
                if result.get('valid') and not result.get('errors') and not result.get('warnings'):
                    sections.append('''
                    <div style="background:#d4edda;border-left:4px solid #28a745;padding:10px;margin:10px 0;border-radius:0 5px 5px 0;">
                        <span style="color:#155724;">Query is valid</span>
                    </div>
                    ''')
                else:
                    errors = ''.join([f'<div style="color:#721c24;">• {e}</div>' for e in result.get('errors', [])])
                    warnings = ''.join([f'<div style="color:#856404;">• {w}</div>' for w in result.get('warnings', [])])
                    bg = '#f8d7da' if result.get('errors') else '#fff3cd'
                    border = '#dc3545' if result.get('errors') else '#ffc107'
                    sections.append(f'''
                    <div style="background:{bg};border-left:4px solid {border};padding:10px;margin:10px 0;border-radius:0 5px 5px 0;">
                        {errors}{warnings}
                    </div>
                    ''')

            # Explanation
            if self.explain_cb.value:
                result = await self.client.explain(query, self.workspace)
                sections.append(f'''
                <div style="background:#e3f2fd;border-left:4px solid #2196f3;padding:10px;margin:10px 0;border-radius:0 5px 5px 0;">
                    <strong style="color:#1565c0;">Explanation</strong>
                    <div style="margin-top:8px;">{result.get("explanation", "N/A")}</div>
                    <div style="margin-top:8px;font-size:0.9em;color:#6c757d;">
                        Complexity: {result.get("complexity", "unknown")} |
                        Tables: {", ".join(result.get("tables", [])) or "N/A"}
                    </div>
                </div>
                ''')

            # Completions
            if self.complete_cb.value:
                result = await self.client.complete(query, self.workspace)
                completions = result.get('completions', [])
                if completions:
                    items = ''
                    for i, c in enumerate(completions[:3], 1):
                        escaped_c = c.replace('<', '&lt;').replace('>', '&gt;')
                        items += f'''
                        <div style="margin:8px 0;">
                            <strong>Option {i}:</strong>
                            <pre style="background:#1e1e1e;color:#d4d4d4;padding:8px;border-radius:4px;margin:5px 0;font-size:0.9em;">{escaped_c}</pre>
                        </div>
                        '''
                    sections.append(f'''
                    <div style="background:#e8f5e9;border-left:4px solid #4caf50;padding:10px;margin:10px 0;border-radius:0 5px 5px 0;">
                        <strong style="color:#2e7d32;">Suggestions</strong>
                        {items}
                    </div>
                    ''')

            display(HTML(''.join(sections)))

    def display(self):
        """Display the widget."""
        display(self.widget)


class QueryHistoryWidget:
    """Widget to display and manage query history."""

    def __init__(
        self,
        workspace: str = "jupyter_widget",
        api_url: str = "http://localhost:8000"
    ):
        self.workspace = workspace
        self.client = L0l1JupyterClient(api_url=api_url)
        self.on_select: Optional[Callable[[str], None]] = None
        self._create_widget()

    def _run_async(self, coro):
        """Run async coroutine."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            try:
                import nest_asyncio
                nest_asyncio.apply()
                return asyncio.get_event_loop().run_until_complete(coro)
            except ImportError:
                return None
        else:
            return asyncio.run(coro)

    def _create_widget(self):
        """Create the widget."""
        self.header = widgets.HTML(
            value='<h3 style="margin:0;color:#667eea;">Query History</h3>'
        )

        self.search_input = widgets.Text(
            placeholder='Search similar queries...',
            layout=widgets.Layout(width='100%')
        )

        self.search_btn = widgets.Button(
            description='Search',
            button_style='primary',
            icon='search',
            layout=widgets.Layout(width='100px')
        )
        self.search_btn.on_click(self._on_search)

        self.results_output = widgets.Output()

        self.widget = widgets.VBox([
            self.header,
            widgets.HBox([self.search_input, self.search_btn]),
            self.results_output
        ], layout=widgets.Layout(padding='15px'))

    def _on_search(self, btn):
        """Handle search."""
        query = self.search_input.value.strip()
        if query:
            self._run_async(self._search(query))

    async def _search(self, query: str):
        """Search for similar queries."""
        self.results_output.clear_output()
        with self.results_output:
            results = await self.client.get_similar_queries(query, self.workspace)

            if not results:
                display(HTML('<div style="color:#6c757d;">No similar queries found</div>'))
                return

            html = '<div style="margin-top:10px;">'
            for i, r in enumerate(results, 1):
                q = r.get('query', '').replace('<', '&lt;').replace('>', '&gt;')
                sim = r.get('similarity', 0)
                html += f'''
                <div style="background:#f8f9fa;padding:10px;margin:5px 0;border-radius:5px;border:1px solid #dee2e6;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
                        <strong>Query {i}</strong>
                        <span style="color:#6c757d;">Similarity: {sim:.0%}</span>
                    </div>
                    <pre style="background:#1e1e1e;color:#d4d4d4;padding:8px;border-radius:4px;margin:0;font-size:0.9em;">{q}</pre>
                </div>
                '''
            html += '</div>'
            display(HTML(html))

    def display(self):
        """Display the widget."""
        display(self.widget)


class SchemaExplorerWidget:
    """Widget to explore database schema."""

    def __init__(self, schema: str = ""):
        self.schema = schema
        self._create_widget()

    def _create_widget(self):
        """Create the widget."""
        self.header = widgets.HTML(
            value='<h3 style="margin:0;color:#667eea;">Schema Explorer</h3>'
        )

        self.schema_input = widgets.Textarea(
            value=self.schema,
            placeholder='Paste your schema SQL here...',
            layout=widgets.Layout(width='100%', height='200px')
        )

        self.parse_btn = widgets.Button(
            description='Parse Schema',
            button_style='primary',
            icon='table',
            layout=widgets.Layout(width='150px')
        )
        self.parse_btn.on_click(self._on_parse)

        self.results_output = widgets.Output()

        self.widget = widgets.VBox([
            self.header,
            self.schema_input,
            self.parse_btn,
            self.results_output
        ], layout=widgets.Layout(padding='15px'))

    def _on_parse(self, btn):
        """Parse and display schema."""
        self.results_output.clear_output()
        schema = self.schema_input.value.strip()

        if not schema:
            with self.results_output:
                display(HTML('<div style="color:#dc3545;">Please enter a schema</div>'))
            return

        with self.results_output:
            # Simple parsing - extract CREATE TABLE statements
            tables = self._extract_tables(schema)

            if not tables:
                display(HTML('<div style="color:#6c757d;">No tables found in schema</div>'))
                return

            html = '<div style="margin-top:10px;">'
            for table_name, columns in tables.items():
                cols_html = ''.join([
                    f'<div style="margin:3px 0;padding-left:15px;"><code>{col}</code></div>'
                    for col in columns
                ])
                html += f'''
                <div style="background:#e3f2fd;padding:10px;margin:5px 0;border-radius:5px;border:1px solid #90caf9;">
                    <strong style="color:#1565c0;">{table_name}</strong>
                    {cols_html}
                </div>
                '''
            html += '</div>'
            display(HTML(html))

    def _extract_tables(self, schema: str) -> dict:
        """Extract table definitions from schema."""
        import re
        tables = {}

        # Simple regex to find CREATE TABLE statements
        pattern = r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s*\((.*?)\)'
        matches = re.findall(pattern, schema, re.IGNORECASE | re.DOTALL)

        for table_name, columns_str in matches:
            # Extract column names (simplified)
            columns = []
            for line in columns_str.split(','):
                line = line.strip()
                if line and not line.upper().startswith(('PRIMARY', 'FOREIGN', 'UNIQUE', 'INDEX', 'CONSTRAINT')):
                    parts = line.split()
                    if parts:
                        columns.append(parts[0])
            tables[table_name] = columns

        return tables

    def display(self):
        """Display the widget."""
        display(self.widget)


# Convenience functions
def create_sql_validator(
    workspace: str = "jupyter_widget",
    api_url: str = "http://localhost:8000"
) -> SQLValidatorWidget:
    """Create and return a SQL validator widget."""
    return SQLValidatorWidget(workspace=workspace, api_url=api_url)


def create_query_history(
    workspace: str = "jupyter_widget",
    api_url: str = "http://localhost:8000"
) -> QueryHistoryWidget:
    """Create and return a query history widget."""
    return QueryHistoryWidget(workspace=workspace, api_url=api_url)


def create_schema_explorer(schema: str = "") -> SchemaExplorerWidget:
    """Create and return a schema explorer widget."""
    return SchemaExplorerWidget(schema=schema)
