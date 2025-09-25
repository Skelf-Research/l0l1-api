import re
from typing import List, Dict, Any, Tuple
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

from ..core.config import settings


class PIIDetector:
    """PII detection and anonymization service."""

    def __init__(self):
        # Initialize Presidio engines
        provider = NlpEngineProvider()
        nlp_configuration = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
        }
        nlp_engine = provider.create_engine(nlp_configuration)

        self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
        self.anonymizer = AnonymizerEngine()

        # Additional SQL-specific PII patterns
        self.sql_patterns = {
            "EMAIL_REGEX": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "PHONE_REGEX": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "SSN_REGEX": r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b',
            "CREDIT_CARD_REGEX": r'\b\d{4}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}\b',
            "IP_ADDRESS_REGEX": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        }

    def detect_pii(self, text: str) -> List[Dict[str, Any]]:
        """Detect PII in text using multiple methods."""
        # Use Presidio for advanced detection
        presidio_results = self.analyzer.analyze(
            text=text,
            entities=settings.pii_entities,
            language="en"
        )

        # Convert to standard format
        pii_findings = []
        for result in presidio_results:
            pii_findings.append({
                "entity_type": result.entity_type,
                "start": result.start,
                "end": result.end,
                "confidence": result.score,
                "text": text[result.start:result.end]
            })

        # Add regex-based detection for SQL-specific patterns
        for pattern_name, pattern in self.sql_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Check if already found by Presidio
                overlapping = any(
                    finding["start"] <= match.start() < finding["end"] or
                    finding["start"] < match.end() <= finding["end"]
                    for finding in pii_findings
                )

                if not overlapping:
                    pii_findings.append({
                        "entity_type": pattern_name.replace("_REGEX", ""),
                        "start": match.start(),
                        "end": match.end(),
                        "confidence": 0.9,
                        "text": match.group()
                    })

        return pii_findings

    def anonymize_sql(self, sql_query: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Anonymize SQL query by removing PII."""
        pii_findings = self.detect_pii(sql_query)

        if not pii_findings:
            return sql_query, []

        # Sort by start position in reverse order for replacement
        pii_findings_sorted = sorted(pii_findings, key=lambda x: x["start"], reverse=True)

        anonymized_query = sql_query
        anonymizations = []

        for finding in pii_findings_sorted:
            entity_type = finding["entity_type"]
            original_text = finding["text"]

            # Generate anonymized replacement based on entity type
            if entity_type in ["EMAIL_ADDRESS", "EMAIL"]:
                replacement = "'user@example.com'"
            elif entity_type in ["PHONE_NUMBER", "PHONE"]:
                replacement = "'555-0123'"
            elif entity_type in ["SSN"]:
                replacement = "'XXX-XX-XXXX'"
            elif entity_type in ["CREDIT_CARD"]:
                replacement = "'XXXX-XXXX-XXXX-XXXX'"
            elif entity_type in ["IP_ADDRESS"]:
                replacement = "'192.168.1.1'"
            elif entity_type in ["PERSON"]:
                replacement = "'John Doe'"
            else:
                replacement = "'[REDACTED]'"

            # Replace in query
            anonymized_query = (
                anonymized_query[:finding["start"]] +
                replacement +
                anonymized_query[finding["end"]:]
            )

            anonymizations.append({
                "entity_type": entity_type,
                "original": original_text,
                "replacement": replacement,
                "position": finding["start"]
            })

        return anonymized_query, anonymizations

    def is_safe_for_learning(self, sql_query: str) -> bool:
        """Check if SQL query is safe to use for learning (no PII)."""
        pii_findings = self.detect_pii(sql_query)
        return len(pii_findings) == 0

    def sanitize_for_learning(self, sql_query: str) -> str:
        """Sanitize SQL query for learning by removing PII."""
        anonymized, _ = self.anonymize_sql(sql_query)
        return anonymized