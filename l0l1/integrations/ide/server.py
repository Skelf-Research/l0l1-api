import asyncio
import logging
from typing import Optional, List
from pygls.server import LanguageServer
from lsprotocol.types import (
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DID_SAVE,
    TEXT_DOCUMENT_COMPLETION,
    TEXT_DOCUMENT_HOVER,
    TEXT_DOCUMENT_CODE_ACTION,
    INITIALIZE,
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
    DidSaveTextDocumentParams,
    CompletionParams,
    HoverParams,
    CodeActionParams,
    InitializeParams,
)

from .protocol import L0L1LanguageServer


class LSPServer:
    """Language Server for l0l1 SQL analysis."""

    def __init__(self):
        self.server = L0L1LanguageServer()
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up LSP message handlers."""

        @self.server.feature(INITIALIZE)
        async def initialize(params: InitializeParams):
            """Initialize the language server."""
            return {
                "capabilities": {
                    "textDocumentSync": 1,  # Full document sync
                    "completionProvider": {
                        "triggerCharacters": [" ", ".", "(", ","]
                    },
                    "hoverProvider": True,
                    "codeActionProvider": True,
                    "diagnosticsProvider": True,
                }
            }

        @self.server.feature(TEXT_DOCUMENT_DID_OPEN)
        async def did_open(params: DidOpenTextDocumentParams):
            """Handle document open event."""
            uri = params.text_document.uri
            text = params.text_document.text

            # Validate document and publish diagnostics
            diagnostics = await self.server.validate_document(uri, text)
            self.server.publish_diagnostics(uri, diagnostics)

        @self.server.feature(TEXT_DOCUMENT_DID_CHANGE)
        async def did_change(params: DidChangeTextDocumentParams):
            """Handle document change event."""
            uri = params.text_document.uri
            document = self.server.workspace.get_document(uri)

            # Validate document and publish diagnostics
            diagnostics = await self.server.validate_document(uri, document.source)
            self.server.publish_diagnostics(uri, diagnostics)

        @self.server.feature(TEXT_DOCUMENT_DID_SAVE)
        async def did_save(params: DidSaveTextDocumentParams):
            """Handle document save event."""
            uri = params.text_document.uri
            document = self.server.workspace.get_document(uri)

            # Re-validate on save
            diagnostics = await self.server.validate_document(uri, document.source)
            self.server.publish_diagnostics(uri, diagnostics)

            # Record successful query for learning (if no validation errors)
            if not any(d.severity.value <= 2 for d in diagnostics):  # No errors or warnings
                workspace_id = self.server._extract_workspace_id(uri)
                try:
                    await self.server.learning_service.record_successful_query(
                        workspace_id=workspace_id,
                        query=document.source,
                        execution_time=0.0,  # Unknown execution time
                        result_count=0,      # Unknown result count
                        schema_context=self.server.workspace_schemas.get(uri)
                    )
                except Exception:
                    pass  # Learning is optional

        @self.server.feature(TEXT_DOCUMENT_COMPLETION)
        async def completion(params: CompletionParams):
            """Handle completion request."""
            return await self.server.provide_completion(params)

        @self.server.feature(TEXT_DOCUMENT_HOVER)
        async def hover(params: HoverParams):
            """Handle hover request."""
            return await self.server.provide_hover(params)

        @self.server.feature(TEXT_DOCUMENT_CODE_ACTION)
        async def code_action(params: CodeActionParams):
            """Handle code action request."""
            return await self.server.provide_code_actions(params)

        # Custom commands for l0l1
        @self.server.command("l0l1.setSchema")
        async def set_schema(params):
            """Set schema context for current document."""
            uri = params[0]["uri"]
            schema = params[0]["schema"]
            self.server.set_workspace_schema(uri, schema)
            return {"status": "success"}

        @self.server.command("l0l1.getLearningStats")
        async def get_learning_stats(params):
            """Get learning statistics."""
            workspace_id = params[0].get("workspace", "default")
            stats = self.server.learning_service.get_learning_stats(workspace_id)
            return stats

        @self.server.command("l0l1.anonymizeQuery")
        async def anonymize_query(params):
            """Anonymize SQL query."""
            query = params[0]["query"]
            anonymized, anonymizations = self.server.pii_detector.anonymize_sql(query)
            return {
                "anonymized_query": anonymized,
                "anonymizations": anonymizations
            }

    def start_tcp(self, host: str = "localhost", port: int = 9257):
        """Start LSP server over TCP."""
        self.server.start_tcp(host, port)

    def start_io(self):
        """Start LSP server over stdin/stdout."""
        self.server.start_io()


def main():
    """Main entry point for the LSP server."""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="l0l1 Language Server")
    parser.add_argument("--tcp", action="store_true", help="Start server over TCP")
    parser.add_argument("--host", default="localhost", help="TCP host (default: localhost)")
    parser.add_argument("--port", type=int, default=9257, help="TCP port (default: 9257)")
    parser.add_argument("--log-level", default="INFO", help="Log level")

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Start server
    server = LSPServer()

    if args.tcp:
        print(f"Starting l0l1 Language Server on {args.host}:{args.port}")
        server.start_tcp(args.host, args.port)
    else:
        print("Starting l0l1 Language Server on stdin/stdout")
        server.start_io()


if __name__ == "__main__":
    main()