"""Test data models."""

import pytest
from static_analyzer.models import (
    SourceLocation, 
    Violation, 
    AnalysisReport,
    RuleMetadata, 
    Standard, 
    Severity, 
    Confidence,
    Deviation
)


class TestSourceLocation:
    def test_source_location_creation(self):
        """Test source location creation."""
        location = SourceLocation(
            file_path="/path/to/file.c",
            line=42,
            column=10
        )
        
        assert location.file_path == "/path/to/file.c"
        assert location.line == 42
        assert location.column == 10
        assert location.end_line is None
        assert location.end_column is None
    
    def test_source_location_with_range(self):
        """Test source location with range information."""
        location = SourceLocation(
            file_path="/path/to/file.c",
            line=42,
            column=10,
            end_line=42,
            end_column=20
        )
        
        assert location.end_line == 42
        assert location.end_column == 20
    
    def test_source_location_str(self):
        """Test string representation of source location."""
        location1 = SourceLocation("/path/to/file.c", 42, 10)
        assert str(location1) == "/path/to/file.c:42:10"
        
        location2 = SourceLocation("/path/to/file.c", 42, 10, 42, 20)
        assert str(location2) == "/path/to/file.c:42:10-42:20"


class TestRuleMetadata:
    def test_rule_metadata_creation(self):
        """Test rule metadata creation."""
        metadata = RuleMetadata(
            id="MISRA-C-2012-8.7",
            standard=Standard.MISRA,
            title="Objects should be defined at block scope",
            description="Test description",
            rationale="Test rationale", 
            severity=Severity.MINOR,
            category="Scope",
            references=["MISRA C:2012 Rule 8.7"]
        )
        
        assert metadata.id == "MISRA-C-2012-8.7"
        assert metadata.standard == Standard.MISRA
        assert metadata.severity == Severity.MINOR
        assert len(metadata.references) == 1
    
    def test_rule_metadata_validation(self):
        """Test rule metadata validation."""
        with pytest.raises(ValueError):
            RuleMetadata(
                id="",  # Empty ID should raise error
                standard=Standard.MISRA,
                title="Test",
                description="Test",
                rationale="Test",
                severity=Severity.MINOR,
                category="Test",
                references=[]
            )
        
        with pytest.raises(ValueError):
            RuleMetadata(
                id="TEST-1",
                standard=Standard.MISRA,
                title="",  # Empty title should raise error
                description="Test",
                rationale="Test",
                severity=Severity.MINOR,
                category="Test",
                references=[]
            )


class TestViolation:
    def test_violation_creation(self):
        """Test violation creation."""
        location = SourceLocation("/path/to/file.c", 42, 10)
        
        violation = Violation(
            rule_id="MISRA-C-2012-8.7",
            standard=Standard.MISRA,
            location=location,
            message="Test violation message",
            severity=Severity.MINOR,
            confidence=Confidence.HIGH
        )
        
        assert violation.rule_id == "MISRA-C-2012-8.7"
        assert violation.standard == Standard.MISRA
        assert violation.location == location
        assert violation.message == "Test violation message"
        assert violation.severity == Severity.MINOR
        assert violation.confidence == Confidence.HIGH
    
    def test_violation_with_ai_fields(self):
        """Test violation with AI-generated fields."""
        location = SourceLocation("/path/to/file.c", 42, 10)
        
        violation = Violation(
            rule_id="CERT-EXP34-C",
            standard=Standard.CERT,
            location=location,
            message="Null pointer dereference",
            severity=Severity.CRITICAL,
            confidence=Confidence.HIGH,
            ai_explanation="This violation occurs because...",
            ai_risk_summary="Risk: system crash",
            ai_suggested_fix="Add null check before dereferencing"
        )
        
        assert violation.ai_explanation == "This violation occurs because..."
        assert violation.ai_risk_summary == "Risk: system crash"
        assert violation.ai_suggested_fix == "Add null check before dereferencing"
    
    def test_violation_validation(self):
        """Test violation validation."""
        location = SourceLocation("/path/to/file.c", 42, 10)
        
        with pytest.raises(ValueError):
            Violation(
                rule_id="",  # Empty rule ID
                standard=Standard.MISRA,
                location=location,
                message="Test",
                severity=Severity.MINOR,
                confidence=Confidence.HIGH
            )
        
        with pytest.raises(ValueError):
            Violation(
                rule_id="TEST-1",
                standard=Standard.MISRA,
                location=location,
                message="",  # Empty message
                severity=Severity.MINOR,
                confidence=Confidence.HIGH
            )


class TestAnalysisReport:
    def test_empty_report(self):
        """Test empty analysis report."""
        report = AnalysisReport([], {}, {})
        
        assert len(report.violations) == 0
        assert report.summary == {}
        assert report.metadata == {}
    
    def test_report_with_violations(self):
        """Test report with violations."""
        location = SourceLocation("/path/to/file.c", 42, 10)
        violation = Violation(
            rule_id="MISRA-C-2012-8.7",
            standard=Standard.MISRA,
            location=location,
            message="Test violation",
            severity=Severity.MINOR,
            confidence=Confidence.HIGH
        )
        
        report = AnalysisReport([violation], {}, {})
        assert len(report.violations) == 1
        
        # Test filtering methods
        misra_violations = report.get_violations_by_standard(Standard.MISRA)
        assert len(misra_violations) == 1
        
        cert_violations = report.get_violations_by_standard(Standard.CERT)
        assert len(cert_violations) == 0
        
        minor_violations = report.get_violations_by_severity(Severity.MINOR)
        assert len(minor_violations) == 1
        
        rule_violations = report.get_violations_by_rule("MISRA-C-2012-8.7")
        assert len(rule_violations) == 1
    
    def test_add_violation(self):
        """Test adding violation to report."""
        report = AnalysisReport([], {}, {})
        
        location = SourceLocation("/path/to/file.c", 42, 10)
        violation = Violation(
            rule_id="CERT-EXP34-C",
            standard=Standard.CERT,
            location=location,
            message="Null pointer dereference",
            severity=Severity.CRITICAL,
            confidence=Confidence.HIGH
        )
        
        report.add_violation(violation)
        assert len(report.violations) == 1
        assert report.violations[0] == violation
    
    def test_generate_summary(self):
        """Test summary generation."""
        location1 = SourceLocation("/path/to/file1.c", 42, 10)
        location2 = SourceLocation("/path/to/file2.c", 100, 5)
        
        violations = [
            Violation("MISRA-C-2012-8.7", Standard.MISRA, location1, 
                     "Test 1", Severity.MINOR, Confidence.HIGH),
            Violation("CERT-EXP34-C", Standard.CERT, location2, 
                     "Test 2", Severity.CRITICAL, Confidence.HIGH),
            Violation("MISRA-C-2012-8.7", Standard.MISRA, location1, 
                     "Test 3", Severity.MINOR, Confidence.HIGH)
        ]
        
        report = AnalysisReport(violations, {}, {})
        report.generate_summary()
        
        summary = report.summary
        assert summary["total_violations"] == 3
        assert summary["by_severity"]["minor"] == 2
        assert summary["by_severity"]["critical"] == 1
        assert summary["by_standard"]["MISRA"] == 2
        assert summary["by_standard"]["CERT"] == 1
        assert summary["by_rule"]["MISRA-C-2012-8.7"] == 2
        assert summary["by_rule"]["CERT-EXP34-C"] == 1
        assert summary["files_analyzed"] == 2


class TestDeviation:
    def test_deviation_creation(self):
        """Test deviation creation."""
        deviation = Deviation(
            rule_id="MISRA-C-2012-8.7",
            file_pattern="legacy/",
            justification="Legacy code",
            approved_by="Architect",
            approval_date="2024-01-15"
        )
        
        assert deviation.rule_id == "MISRA-C-2012-8.7"
        assert deviation.file_pattern == "legacy/"
        assert deviation.justification == "Legacy code"
        assert deviation.approved_by == "Architect"
        assert deviation.approval_date == "2024-01-15"
        assert deviation.expiry_date is None
        assert deviation.line_ranges is None
    
    def test_deviation_applicability(self):
        """Test deviation applicability checking."""
        deviation = Deviation(
            rule_id="MISRA-C-2012-8.7",
            file_pattern="legacy/",
            justification="Legacy code",
            approved_by="Architect",
            approval_date="2024-01-15"
        )
        
        # Mock violation that matches
        class MockViolation:
            def __init__(self, rule_id, file_path, line=10):
                self.rule_id = rule_id
                self.location = MockLocation(file_path, line)
        
        class MockLocation:
            def __init__(self, file_path, line):
                self.file_path = file_path
                self.line = line
        
        # Should match
        matching_violation = MockViolation("MISRA-C-2012-8.7", "legacy/old_code.c")
        assert deviation.is_applicable(matching_violation)
        
        # Wrong rule ID
        wrong_rule = MockViolation("CERT-EXP34-C", "legacy/old_code.c")
        assert not deviation.is_applicable(wrong_rule)
        
        # Wrong file pattern
        wrong_file = MockViolation("MISRA-C-2012-8.7", "new_code.c")
        assert not deviation.is_applicable(wrong_file)
    
    def test_deviation_with_line_ranges(self):
        """Test deviation with line range restrictions."""
        deviation = Deviation(
            rule_id="CERT-EXP34-C",
            file_pattern="drivers/",
            justification="Hardware drivers",
            approved_by="Safety Manager",
            approval_date="2024-01-20",
            line_ranges=[(100, 150), (200, 250)]
        )
        
        class MockViolation:
            def __init__(self, rule_id, file_path, line):
                self.rule_id = rule_id
                self.location = MockLocation(file_path, line)
        
        class MockLocation:
            def __init__(self, file_path, line):
                self.file_path = file_path
                self.line = line
        
        # Should match - line 125 is in range 100-150
        violation_in_range = MockViolation("CERT-EXP34-C", "drivers/uart.c", 125)
        assert deviation.is_applicable(violation_in_range)
        
        # Should match - line 225 is in range 200-250
        violation_in_range2 = MockViolation("CERT-EXP34-C", "drivers/uart.c", 225)
        assert deviation.is_applicable(violation_in_range2)
        
        # Should not match - line 75 is not in any range
        violation_out_of_range = MockViolation("CERT-EXP34-C", "drivers/uart.c", 75)
        assert not deviation.is_applicable(violation_out_of_range)
