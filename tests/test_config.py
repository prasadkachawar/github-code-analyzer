"""Test configuration management."""

import pytest
import tempfile
import os
from pathlib import Path

from static_analyzer.config import AnalyzerConfig, DeviationManager, create_default_config_file
from static_analyzer.models import Standard


class TestAnalyzerConfig:
    def test_default_config(self):
        """Test default configuration creation."""
        config = AnalyzerConfig.create_default()
        
        assert "MISRA" in config.config["standards"]
        assert "CERT" in config.config["standards"]
        assert "MISRA-C-2012-8.7" in config.config["rules"]["enabled"]
        assert config.config["output"]["format"] == "json"
        assert config.config["ai_assistant"]["enabled"] is False
    
    def test_config_from_dict(self):
        """Test configuration creation from dictionary."""
        config_dict = {
            "standards": ["MISRA"],
            "rules": {"enabled": ["MISRA-C-2012-8.7"]},
            "ai_assistant": {"enabled": True}
        }
        
        config = AnalyzerConfig(config_dict)
        
        standards = config.get_enabled_standards()
        assert len(standards) == 1
        assert standards[0] == Standard.MISRA
        
        assert config.get_enabled_rules() == ["MISRA-C-2012-8.7"]
        assert config.is_ai_enabled() is True
    
    def test_config_from_file(self):
        """Test configuration loading from YAML file."""
        config_content = """
standards:
  - MISRA
  - CERT
rules:
  enabled:
    - MISRA-C-2012-8.7
    - CERT-EXP34-C
  disabled: []
ai_assistant:
  enabled: false
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_file = f.name
        
        try:
            config = AnalyzerConfig.from_file(config_file)
            
            standards = config.get_enabled_standards()
            assert len(standards) == 2
            assert Standard.MISRA in standards
            assert Standard.CERT in standards
            
            enabled_rules = config.get_enabled_rules()
            assert "MISRA-C-2012-8.7" in enabled_rules
            assert "CERT-EXP34-C" in enabled_rules
            
        finally:
            os.unlink(config_file)
    
    def test_save_config_to_file(self):
        """Test saving configuration to file."""
        config = AnalyzerConfig.create_default()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_file = f.name
        
        try:
            config.save_to_file(config_file)
            
            # Load it back and verify
            loaded_config = AnalyzerConfig.from_file(config_file)
            assert loaded_config.get_enabled_standards() == config.get_enabled_standards()
            assert loaded_config.get_enabled_rules() == config.get_enabled_rules()
            
        finally:
            if os.path.exists(config_file):
                os.unlink(config_file)


class TestDeviationManager:
    def test_empty_deviation_manager(self):
        """Test deviation manager with no deviations."""
        manager = DeviationManager()
        
        assert len(manager.deviations) == 0
        
        # Mock violation for testing
        class MockViolation:
            def __init__(self):
                self.rule_id = "MISRA-C-2012-8.7"
                self.location = MockLocation()
        
        class MockLocation:
            def __init__(self):
                self.file_path = "test.c"
                self.line = 10
        
        violation = MockViolation()
        is_suppressed, _ = manager.is_violation_suppressed(violation)
        assert not is_suppressed
    
    def test_deviation_loading(self):
        """Test loading deviations from YAML file."""
        deviation_content = """
deviations:
  - rule_id: "MISRA-C-2012-8.7"
    file_pattern: "legacy/"
    justification: "Legacy code"
    approved_by: "Architect"
    approval_date: "2024-01-15"
    expiry_date: "2024-12-31"
  - rule_id: "CERT-EXP34-C"
    file_pattern: "drivers/"
    justification: "Hardware drivers"
    approved_by: "Safety Manager"
    approval_date: "2024-01-20"
    line_ranges: [[100, 150]]
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(deviation_content)
            deviation_file = f.name
        
        try:
            manager = DeviationManager(deviation_file)
            
            assert len(manager.deviations) == 2
            
            # Check first deviation
            dev1 = manager.deviations[0]
            assert dev1.rule_id == "MISRA-C-2012-8.7"
            assert dev1.file_pattern == "legacy/"
            assert dev1.justification == "Legacy code"
            assert dev1.approved_by == "Architect"
            
            # Check second deviation
            dev2 = manager.deviations[1]
            assert dev2.rule_id == "CERT-EXP34-C"
            assert dev2.line_ranges == [[100, 150]]
            
        finally:
            os.unlink(deviation_file)
    
    def test_create_sample_deviations(self):
        """Test creation of sample deviations file."""
        manager = DeviationManager()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            sample_file = f.name
        
        try:
            manager.create_sample_deviations_file(sample_file)
            
            # Verify file was created and has content
            assert os.path.exists(sample_file)
            
            with open(sample_file, 'r') as f:
                content = f.read()
                assert "deviations:" in content
                assert "MISRA-C-2012-8.7" in content
                assert "CERT-EXP34-C" in content
            
        finally:
            if os.path.exists(sample_file):
                os.unlink(sample_file)


def test_create_default_config_file():
    """Test creation of default configuration file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config_file = f.name
    
    try:
        create_default_config_file(config_file)
        
        # Verify file was created
        assert os.path.exists(config_file)
        
        # Verify content
        with open(config_file, 'r') as f:
            content = f.read()
            assert "standards:" in content
            assert "MISRA" in content
            assert "CERT" in content
            assert "ai_assistant:" in content
        
        # Verify we can load it as a valid config
        config = AnalyzerConfig.from_file(config_file)
        assert len(config.get_enabled_standards()) > 0
        
    finally:
        if os.path.exists(config_file):
            os.unlink(config_file)
