"""l0l1 Jupyter integration.

This module provides magic commands and widgets for SQL analysis in Jupyter notebooks.

Usage:
    # Load the extension
    %load_ext l0l1.integrations.jupyter

    # Configure settings
    %l0l1_config --workspace myproject --provider openai

    # Analyze SQL
    %%l0l1_sql --validate --explain
    SELECT * FROM users WHERE id = 1

    # Use widgets
    from l0l1.integrations.jupyter.widgets import create_sql_validator
    validator = create_sql_validator()
    validator.display()
"""

from .magic import L0L1Magic, load_ipython_extension, unload_ipython_extension
from .client import L0l1JupyterClient
from .widgets import (
    SQLValidatorWidget,
    QueryHistoryWidget,
    SchemaExplorerWidget,
    create_sql_validator,
    create_query_history,
    create_schema_explorer,
)

__all__ = [
    # Magic commands
    "L0L1Magic",
    "load_ipython_extension",
    "unload_ipython_extension",
    # Client
    "L0l1JupyterClient",
    # Widgets
    "SQLValidatorWidget",
    "QueryHistoryWidget",
    "SchemaExplorerWidget",
    # Factory functions
    "create_sql_validator",
    "create_query_history",
    "create_schema_explorer",
]
