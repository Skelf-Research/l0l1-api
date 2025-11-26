"""SQL validation handlers for the IDE integration."""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ValidationIssue:
    """Represents a validation issue found in SQL."""

    message: str
    severity: str = "warning"  # "error", "warning", "info"
    line: Optional[int] = None
    column: Optional[int] = None
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    code: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message": self.message,
            "severity": self.severity,
            "line": self.line,
            "column": self.column,
            "end_line": self.end_line,
            "end_column": self.end_column,
            "code": self.code,
        }


@dataclass
class ValidationResult:
    """Result of SQL validation."""

    is_valid: bool
    issues: List[ValidationIssue]
    suggestions: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "issues": [i.to_dict() for i in self.issues],
            "suggestions": self.suggestions,
        }


class SQLValidationHandler:
    """Handles SQL validation for IDE integration."""

    def __init__(self, model=None, pii_detector=None):
        self.model = model
        self.pii_detector = pii_detector

    async def validate(
        self,
        sql: str,
        schema_context: Optional[str] = None
    ) -> ValidationResult:
        """Validate SQL query and return issues."""
        issues: List[ValidationIssue] = []
        suggestions: List[str] = []
        is_valid = True

        # Basic syntax validation
        syntax_issues = self._check_syntax(sql)
        issues.extend(syntax_issues)
        if any(i.severity == "error" for i in syntax_issues):
            is_valid = False

        # PII detection
        if self.pii_detector:
            pii_issues = self._check_pii(sql)
            issues.extend(pii_issues)

        # AI-powered validation
        if self.model:
            try:
                ai_result = await self.model.validate_sql_query(sql, schema_context)
                if not ai_result.get("is_valid", True):
                    is_valid = False
                    for issue in ai_result.get("issues", []):
                        issues.append(ValidationIssue(
                            message=str(issue),
                            severity=ai_result.get("severity", "warning")
                        ))
                suggestions = ai_result.get("suggestions", [])
            except Exception:
                pass  # AI validation is optional

        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            suggestions=suggestions
        )

    def _check_syntax(self, sql: str) -> List[ValidationIssue]:
        """Basic SQL syntax checking."""
        issues: List[ValidationIssue] = []

        # Simple checks - in production, use a proper SQL parser
        sql_upper = sql.upper().strip()

        # Check for common issues
        if not sql_upper:
            issues.append(ValidationIssue(
                message="Empty SQL query",
                severity="error",
                line=1,
                column=0
            ))
            return issues

        # Check for unclosed quotes
        single_quotes = sql.count("'")
        if single_quotes % 2 != 0:
            issues.append(ValidationIssue(
                message="Unclosed single quote",
                severity="error"
            ))

        double_quotes = sql.count('"')
        if double_quotes % 2 != 0:
            issues.append(ValidationIssue(
                message="Unclosed double quote",
                severity="error"
            ))

        # Check for unclosed parentheses
        open_parens = sql.count("(")
        close_parens = sql.count(")")
        if open_parens != close_parens:
            issues.append(ValidationIssue(
                message=f"Mismatched parentheses: {open_parens} open, {close_parens} close",
                severity="error"
            ))

        # Best practice warnings
        if "SELECT *" in sql_upper:
            issues.append(ValidationIssue(
                message="Avoid SELECT * - specify columns explicitly",
                severity="info"
            ))

        if "SELECT" in sql_upper and "LIMIT" not in sql_upper and "COUNT" not in sql_upper:
            issues.append(ValidationIssue(
                message="Consider adding LIMIT clause to prevent large result sets",
                severity="info"
            ))

        return issues

    def _check_pii(self, sql: str) -> List[ValidationIssue]:
        """Check for PII in SQL query."""
        issues: List[ValidationIssue] = []

        if not self.pii_detector:
            return issues

        try:
            findings = self.pii_detector.detect_pii(sql)
            for finding in findings:
                issues.append(ValidationIssue(
                    message=f"PII detected: {finding['entity_type']} - consider anonymizing",
                    severity="warning",
                    line=finding.get("line"),
                    column=finding.get("start")
                ))
        except Exception:
            pass  # PII detection is optional

        return issues
