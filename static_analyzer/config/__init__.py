"""Configuration management for static analyzer."""

import yaml
from typing import Dict, List, Optional, Any
from pathlib import Path
from ..models import Deviation, Standard


class AnalyzerConfig:
    """Configuration for static analyzer."""
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """Initialize configuration.
        
        Args:
            config_dict: Configuration dictionary
        """
        self.config = config_dict or {}
        self._load_defaults()
    
    def _load_defaults(self) -> None:
        """Load default configuration values."""
        defaults = {
            "standards": ["MISRA", "CERT"],
            "rules": {
                "enabled": [
                    "MISRA-C-2012-8.7",
                    "MISRA-C-2012-10.1", 
                    "MISRA-C-2012-16.4",
                    "CERT-EXP34-C",
                    "CERT-ARR30-C"
                ],
                "disabled": []
            },
            "output": {
                "format": "json",
                "include_source_context": True,
                "include_metadata": True
            },
            "analysis": {
                "include_paths": [],
                "exclude_paths": [],
                "max_violations_per_rule": 1000,
                "confidence_threshold": "low"
            },
            "ai_assistant": {
                "enabled": False,
                "model": "gpt-4",
                "api_key_env": "OPENAI_API_KEY",
                "max_tokens": 500,
                "temperature": 0.1
            }
        }
        
        # Merge defaults with provided config
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
            elif isinstance(value, dict) and isinstance(self.config[key], dict):
                # Merge nested dictionaries
                for nested_key, nested_value in value.items():
                    if nested_key not in self.config[key]:
                        self.config[key][nested_key] = nested_value
    
    @classmethod
    def from_file(cls, config_path: str) -> 'AnalyzerConfig':
        """Load configuration from YAML file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            AnalyzerConfig instance
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)
        
        return cls(config_dict)
    
    @classmethod
    def create_default(cls) -> 'AnalyzerConfig':
        """Create default configuration.
        
        Returns:
            AnalyzerConfig instance with defaults
        """
        return cls({})
    
    def get_enabled_standards(self) -> List[Standard]:
        """Get list of enabled standards.
        
        Returns:
            List of enabled Standard enums
        """
        standard_names = self.config.get("standards", [])
        standards = []
        
        for name in standard_names:
            try:
                standards.append(Standard[name])
            except KeyError:
                print(f"Warning: Unknown standard '{name}' ignored")
        
        return standards
    
    def get_enabled_rules(self) -> List[str]:
        """Get list of enabled rule IDs.
        
        Returns:
            List of rule ID strings
        """
        return self.config.get("rules", {}).get("enabled", [])
    
    def get_disabled_rules(self) -> List[str]:
        """Get list of disabled rule IDs.
        
        Returns:
            List of rule ID strings
        """
        return self.config.get("rules", {}).get("disabled", [])
    
    def get_include_paths(self) -> List[str]:
        """Get list of include paths for compilation.
        
        Returns:
            List of include path strings
        """
        return self.config.get("analysis", {}).get("include_paths", [])
    
    def get_exclude_paths(self) -> List[str]:
        """Get list of paths to exclude from analysis.
        
        Returns:
            List of exclude path patterns
        """
        return self.config.get("analysis", {}).get("exclude_paths", [])
    
    def is_ai_enabled(self) -> bool:
        """Check if AI assistant is enabled.
        
        Returns:
            True if AI assistant is enabled
        """
        return self.config.get("ai_assistant", {}).get("enabled", False)
    
    def get_ai_config(self) -> Dict[str, Any]:
        """Get AI assistant configuration.
        
        Returns:
            AI configuration dictionary
        """
        return self.config.get("ai_assistant", {})
    
    def get_output_config(self) -> Dict[str, Any]:
        """Get output configuration.
        
        Returns:
            Output configuration dictionary
        """
        return self.config.get("output", {})
    
    def save_to_file(self, config_path: str) -> None:
        """Save configuration to YAML file.
        
        Args:
            config_path: Path to save configuration
        """
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, indent=2)


class DeviationManager:
    """Manages rule deviations/suppressions."""
    
    def __init__(self, deviations_file: Optional[str] = None):
        """Initialize deviation manager.
        
        Args:
            deviations_file: Path to deviations YAML file
        """
        self.deviations: List[Deviation] = []
        
        if deviations_file:
            self.load_deviations(deviations_file)
    
    def load_deviations(self, deviations_file: str) -> None:
        """Load deviations from YAML file.
        
        Args:
            deviations_file: Path to deviations file
        """
        deviation_path = Path(deviations_file)
        if not deviation_path.exists():
            print(f"Warning: Deviations file not found: {deviations_file}")
            return
        
        try:
            with open(deviation_path, 'r', encoding='utf-8') as f:
                deviations_data = yaml.safe_load(f)
            
            self.deviations = []
            for dev_dict in deviations_data.get("deviations", []):
                deviation = Deviation(
                    rule_id=dev_dict["rule_id"],
                    file_pattern=dev_dict["file_pattern"],
                    justification=dev_dict["justification"],
                    approved_by=dev_dict["approved_by"],
                    approval_date=dev_dict["approval_date"],
                    expiry_date=dev_dict.get("expiry_date"),
                    line_ranges=dev_dict.get("line_ranges")
                )
                self.deviations.append(deviation)
        
        except Exception as e:
            print(f"Error loading deviations: {str(e)}")
    
    def is_violation_suppressed(self, violation) -> tuple[bool, Optional[Deviation]]:
        """Check if a violation is suppressed by any deviation.
        
        Args:
            violation: Violation to check
            
        Returns:
            Tuple of (is_suppressed, matching_deviation)
        """
        for deviation in self.deviations:
            if deviation.is_applicable(violation):
                # TODO: Check expiry date
                return True, deviation
        
        return False, None
    
    def get_applicable_deviations(self, rule_id: str, file_path: str) -> List[Deviation]:
        """Get all deviations applicable to a rule and file.
        
        Args:
            rule_id: Rule identifier
            file_path: Source file path
            
        Returns:
            List of applicable deviations
        """
        applicable = []
        for deviation in self.deviations:
            if (deviation.rule_id == rule_id and 
                deviation.file_pattern in file_path):
                applicable.append(deviation)
        
        return applicable
    
    def create_sample_deviations_file(self, file_path: str) -> None:
        """Create a sample deviations file.
        
        Args:
            file_path: Path where to create the sample file
        """
        sample_deviations = {
            "deviations": [
                {
                    "rule_id": "MISRA-C-2012-8.7",
                    "file_pattern": "legacy_code.c",
                    "justification": "Legacy code - refactoring planned for next release",
                    "approved_by": "Senior Architect",
                    "approval_date": "2024-01-15",
                    "expiry_date": "2024-12-31"
                },
                {
                    "rule_id": "CERT-EXP34-C",
                    "file_pattern": "drivers/",
                    "justification": "Hardware drivers require specific null pointer handling",
                    "approved_by": "Safety Manager", 
                    "approval_date": "2024-01-20",
                    "line_ranges": [[100, 150], [200, 250]]
                }
            ]
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(sample_deviations, f, default_flow_style=False, indent=2)


# Configuration file templates
DEFAULT_CONFIG_TEMPLATE = """
# Static Analyzer Configuration
# Generated automatically - customize as needed

# Enabled coding standards
standards:
  - MISRA
  - CERT

# Rule configuration
rules:
  enabled:
    - MISRA-C-2012-8.7
    - MISRA-C-2012-10.1
    - MISRA-C-2012-16.4
    - CERT-EXP34-C
    - CERT-ARR30-C
  disabled: []

# Analysis settings
analysis:
  include_paths: []
  exclude_paths:
    - "**/test/**"
    - "**/tests/**" 
    - "**/*_test.c"
  max_violations_per_rule: 1000
  confidence_threshold: "low"  # low, medium, high

# Output configuration
output:
  format: "json"  # json, yaml, csv
  include_source_context: true
  include_metadata: true

# AI Assistant (optional)
ai_assistant:
  enabled: false
  model: "gpt-4"
  api_key_env: "OPENAI_API_KEY"
  max_tokens: 500
  temperature: 0.1
"""


def create_default_config_file(file_path: str) -> None:
    """Create default configuration file.
    
    Args:
        file_path: Path where to create the config file
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(DEFAULT_CONFIG_TEMPLATE.strip())
