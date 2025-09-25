import asyncio
from typing import List, Optional, Dict, Any
from pygls.server import LanguageServer
from lsprotocol.types import (
    CompletionItem,
    CompletionList,
    CompletionParams,
    Diagnostic,
    DiagnosticSeverity,
    Hover,
    HoverParams,
    Position,
    Range,
    TextDocumentPositionParams,
    CodeAction,
    CodeActionParams,
)

from ...models.factory import ModelFactory
from ...services.pii_detector import PIIDetector
from ...services.learning_service import LearningService
from ...core.config import settings


class L0L1LanguageServer(LanguageServer):
    """Language Server Protocol implementation for l0l1 SQL analysis."""

    def __init__(self):
        super().__init__("l0l1-lsp", "v0.2.0")
        self.model = ModelFactory.get_default_model()
        self.pii_detector = PIIDetector()
        self.learning_service = LearningService()
        self.workspace_schemas = {}  # Cache for workspace schemas

    async def validate_document(self, uri: str, text: str) -> List[Diagnostic]:
        """Validate SQL document and return diagnostics."""
        diagnostics = []

        try:
            # Check for PII first
            if settings.enable_pii_detection:
                pii_findings = self.pii_detector.detect_pii(text)
                for finding in pii_findings:
                    start_pos = self._offset_to_position(text, finding["start"])
                    end_pos = self._offset_to_position(text, finding["end"])

                    diagnostics.append(Diagnostic(
                        range=Range(start=start_pos, end=end_pos),
                        message=f"PII detected: {finding['entity_type']} - {finding['text']}",
                        severity=DiagnosticSeverity.Warning,
                        source="l0l1-pii"
                    ))

            # Validate SQL syntax and logic
            schema_context = self.workspace_schemas.get(uri)
            validation_result = await self.model.validate_sql_query(text, schema_context)

            if not validation_result.get("is_valid", True):
                severity_map = {
                    "low": DiagnosticSeverity.Information,
                    "medium": DiagnosticSeverity.Warning,
                    "high": DiagnosticSeverity.Error
                }
                severity = severity_map.get(validation_result.get("severity", "medium"), DiagnosticSeverity.Warning)

                # For now, highlight the entire document
                # In a real implementation, you'd parse the SQL to get specific locations
                start_pos = Position(line=0, character=0)
                lines = text.split('\n')
                end_pos = Position(line=len(lines) - 1, character=len(lines[-1]) if lines else 0)

                for issue in validation_result.get("issues", []):
                    diagnostics.append(Diagnostic(
                        range=Range(start=start_pos, end=end_pos),
                        message=f"SQL Issue: {issue}",
                        severity=severity,
                        source="l0l1-validation"
                    ))

        except Exception as e:
            # Add diagnostic for analysis errors
            start_pos = Position(line=0, character=0)
            lines = text.split('\n')
            end_pos = Position(line=len(lines) - 1, character=len(lines[-1]) if lines else 0)

            diagnostics.append(Diagnostic(
                range=Range(start=start_pos, end=end_pos),
                message=f"l0l1 Analysis Error: {str(e)}",
                severity=DiagnosticSeverity.Information,
                source="l0l1-error"
            ))

        return diagnostics

    async def provide_completion(self, params: CompletionParams) -> Optional[CompletionList]:
        """Provide SQL completion suggestions."""
        try:
            uri = params.text_document.uri
            position = params.position

            # Get document text up to cursor position
            document = self.workspace.get_document(uri)
            text = document.source
            lines = text.split('\n')

            # Get partial query up to cursor
            partial_lines = lines[:position.line + 1]
            if partial_lines:
                partial_lines[-1] = partial_lines[-1][:position.character]
            partial_query = '\n'.join(partial_lines)

            # Get completions from learning service
            workspace_id = self._extract_workspace_id(uri)
            schema_context = self.workspace_schemas.get(uri)

            suggestions = await self.learning_service.get_query_suggestions(
                partial_query, workspace_id, schema_context
            )

            # Convert to completion items
            completion_items = []
            for i, suggestion in enumerate(suggestions):
                completion_items.append(CompletionItem(
                    label=f"Suggestion {i + 1}",
                    detail=suggestion[:100] + "..." if len(suggestion) > 100 else suggestion,
                    documentation=f"AI-generated SQL completion",
                    insert_text=suggestion,
                    sort_text=f"00{i}"  # Ensure our suggestions appear first
                ))

            return CompletionList(is_incomplete=False, items=completion_items)

        except Exception:
            return None

    async def provide_hover(self, params: HoverParams) -> Optional[Hover]:
        """Provide hover information for SQL elements."""
        try:
            uri = params.text_document.uri
            document = self.workspace.get_document(uri)
            text = document.source

            # Get word at position
            word = self._get_word_at_position(text, params.position)
            if not word:
                return None

            # Try to explain the SQL query
            schema_context = self.workspace_schemas.get(uri)
            explanation = await self.model.explain_sql_query(text, schema_context)

            return Hover(
                contents=f"**l0l1 Query Analysis**\n\n{explanation}",
                range=self._get_word_range(text, params.position)
            )

        except Exception:
            return None

    async def provide_code_actions(self, params: CodeActionParams) -> List[CodeAction]:
        """Provide code actions for SQL improvements."""
        actions = []
        try:
            uri = params.text_document.uri
            document = self.workspace.get_document(uri)
            text = document.source

            # Check if there are validation issues in the range
            for diagnostic in params.context.diagnostics:
                if diagnostic.source == "l0l1-validation":
                    # Offer to correct the query
                    workspace_id = self._extract_workspace_id(uri)
                    schema_context = self.workspace_schemas.get(uri)

                    improved = await self.learning_service.improve_query_with_learning(
                        text, workspace_id, diagnostic.message, schema_context
                    )

                    if improved["improved_query"] != text:
                        actions.append(CodeAction(
                            title="🔧 Fix SQL with l0l1",
                            kind="quickfix",
                            edit={
                                "changes": {
                                    uri: [{
                                        "range": Range(
                                            start=Position(line=0, character=0),
                                            end=Position(line=len(text.split('\n')), character=0)
                                        ),
                                        "newText": improved["improved_query"]
                                    }]
                                }
                            }
                        ))

                elif diagnostic.source == "l0l1-pii":
                    # Offer to anonymize PII
                    anonymized, _ = self.pii_detector.anonymize_sql(text)
                    if anonymized != text:
                        actions.append(CodeAction(
                            title="🔒 Anonymize PII with l0l1",
                            kind="quickfix",
                            edit={
                                "changes": {
                                    uri: [{
                                        "range": Range(
                                            start=Position(line=0, character=0),
                                            end=Position(line=len(text.split('\n')), character=0)
                                        ),
                                        "newText": anonymized
                                    }]
                                }
                            }
                        ))

        except Exception:
            pass

        return actions

    def set_workspace_schema(self, uri: str, schema: str):
        """Set schema context for a workspace/document."""
        self.workspace_schemas[uri] = schema

    def _offset_to_position(self, text: str, offset: int) -> Position:
        """Convert byte offset to LSP Position."""
        lines = text[:offset].split('\n')
        return Position(line=len(lines) - 1, character=len(lines[-1]))

    def _get_word_at_position(self, text: str, position: Position) -> Optional[str]:
        """Get word at the given position."""
        lines = text.split('\n')
        if position.line >= len(lines):
            return None

        line = lines[position.line]
        if position.character >= len(line):
            return None

        # Simple word extraction - in a real implementation, you'd use proper SQL parsing
        import re
        words = re.findall(r'\b\w+\b', line)
        char_pos = 0
        for word in words:
            start = line.find(word, char_pos)
            end = start + len(word)
            if start <= position.character < end:
                return word
            char_pos = end

        return None

    def _get_word_range(self, text: str, position: Position) -> Optional[Range]:
        """Get range of word at position."""
        lines = text.split('\n')
        if position.line >= len(lines):
            return None

        line = lines[position.line]
        if position.character >= len(line):
            return None

        # Find word boundaries
        start = position.character
        while start > 0 and line[start - 1].isalnum():
            start -= 1

        end = position.character
        while end < len(line) and line[end].isalnum():
            end += 1

        return Range(
            start=Position(line=position.line, character=start),
            end=Position(line=position.line, character=end)
        )

    def _extract_workspace_id(self, uri: str) -> str:
        """Extract workspace ID from document URI."""
        # Simple implementation - extract from file path
        # In a real implementation, you'd have better workspace detection
        import os
        return os.path.basename(os.path.dirname(uri)) or "default"