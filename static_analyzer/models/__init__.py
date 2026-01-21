"""Data models for static analysis violations and metadata."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses_json import dataclass_json
import json


class Severity(Enum):
    """Violation severity levels."""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFO = "info"


class Standard(Enum):
    """Supported coding standards."""
    MISRA = "MISRA"
    CERT = "CERT"


class Confidence(Enum):
    """Confidence level in violation detection."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass_json
@dataclass(frozen=True)
class SourceLocation:
    """Source code location information."""
    file_path: str
    line: int
    column: int
    end_line: Optional[int] = None
    end_column: Optional[int] = None

    def __str__(self) -> str:
        if self.end_line and self.end_column:
            return f"{self.file_path}:{self.line}:{self.column}-{self.end_line}:{self.end_column}"
        return f"{self.file_path}:{self.line}:{self.column}"


@dataclass_json
@dataclass
class RuleMetadata:
    """Metadata for a static analysis rule."""
    id: str
    standard: Standard
    title: str
    description: str
    rationale: str
    severity: Severity
    category: str
    references: List[str]

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Rule ID cannot be empty")
        if not self.title:
            raise ValueError("Rule title cannot be empty")


@dataclass_json
@dataclass
class Violation:
    """Represents a single static analysis violation."""
    rule_id: str
    standard: Standard
    location: SourceLocation
    message: str
    severity: Severity
    confidence: Confidence
    source_context: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # AI-generated fields (optional)
    ai_explanation: Optional[str] = None
    ai_risk_summary: Optional[str] = None
    ai_suggested_fix: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.rule_id:
            raise ValueError("Rule ID cannot be empty")
        if not self.message:
            raise ValueError("Violation message cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """Convert violation to dictionary format."""
        return self.to_dict()

    def to_json(self) -> str:
        """Convert violation to JSON string."""
        return self.to_json()


@dataclass_json
@dataclass
class AnalysisReport:
    """Complete analysis report containing all violations."""
    violations: List[Violation]
    summary: Dict[str, Any]
    metadata: Dict[str, Any]
    
    def __post_init__(self) -> None:
        if self.violations is None:
            self.violations = []
        if self.summary is None:
            self.summary = {}
        if self.metadata is None:
            self.metadata = {}

    def add_violation(self, violation: Violation) -> None:
        """Add a violation to the report."""
        self.violations.append(violation)

    def get_violations_by_severity(self, severity: Severity) -> List[Violation]:
        """Get all violations of a specific severity."""
        return [v for v in self.violations if v.severity == severity]

    def get_violations_by_standard(self, standard: Standard) -> List[Violation]:
        """Get all violations from a specific standard."""
        return [v for v in self.violations if v.standard == standard]

    def get_violations_by_rule(self, rule_id: str) -> List[Violation]:
        """Get all violations for a specific rule."""
        return [v for v in self.violations if v.rule_id == rule_id]

    def generate_summary(self) -> None:
        """Generate summary statistics."""
        total_violations = len(self.violations)
        
        severity_counts = {
            severity.value: len(self.get_violations_by_severity(severity))
            for severity in Severity
        }
        
        standard_counts = {
            standard.value: len(self.get_violations_by_standard(standard))
            for standard in Standard
        }
        
        rule_counts = {}
        for violation in self.violations:
            rule_counts[violation.rule_id] = rule_counts.get(violation.rule_id, 0) + 1

        self.summary = {
            "total_violations": total_violations,
            "by_severity": severity_counts,
            "by_standard": standard_counts,
            "by_rule": rule_counts,
            "files_analyzed": len(set(v.location.file_path for v in self.violations))
        }

    def to_json_file(self, file_path: str) -> None:
        """Save report to JSON file."""
        self.generate_summary()
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    def to_json(self) -> str:
        """Convert report to JSON string."""
        self.generate_summary()
        return json.dumps(self.to_dict(), indent=2)


@dataclass_json
@dataclass
class Deviation:
    """Rule deviation/suppression configuration."""
    rule_id: str
    file_pattern: str
    justification: str
    approved_by: str
    approval_date: str
    expiry_date: Optional[str] = None
    line_ranges: Optional[List[tuple]] = None
    
    def is_applicable(self, violation: Violation) -> bool:
        """Check if this deviation applies to a given violation."""
        if violation.rule_id != self.rule_id:
            return False
            
        # Simple pattern matching (could be enhanced with regex)
        if self.file_pattern not in violation.location.file_path:
            return False
            
        # Check line ranges if specified
        if self.line_ranges:
            violation_line = violation.location.line
            for start_line, end_line in self.line_ranges:
                if start_line <= violation_line <= end_line:
                    return True
            return False
            
        return True
