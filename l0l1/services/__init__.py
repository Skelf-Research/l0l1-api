# Core services (no external dependencies)
from .pattern_store import PatternStore
from .database_service import DatabaseService, DatabaseConnection, ConnectionStore

# Services with optional dependencies
try:
    from .pii_detector import PIIDetector
except ImportError:
    PIIDetector = None

try:
    from .learning_service import LearningService
except ImportError:
    LearningService = None

try:
    from .workspace_service import WorkspaceService
except ImportError:
    WorkspaceService = None

try:
    from .schema_service import SchemaService
except ImportError:
    SchemaService = None

__all__ = [
    "PatternStore",
    "DatabaseService",
    "DatabaseConnection",
    "ConnectionStore",
    "PIIDetector",
    "LearningService",
    "WorkspaceService",
    "SchemaService",
]
