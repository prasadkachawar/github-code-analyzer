"""
Static Code Analysis Framework for Embedded C/C++

A production-quality static analysis framework designed for automotive and
safety-critical embedded applications.

Features:
- AST-based analysis using Clang/libclang  
- MISRA C:2012 and CERT C/C++ rule implementations
- Deterministic, audit-ready results
- CI/CD integration with GitHub Actions
- Optional AI-assisted explanations
- Deviation management with justification tracking

Example usage:
    from static_analyzer import StaticAnalyzer, AnalyzerConfig
    
    # Create analyzer with default configuration
    analyzer = StaticAnalyzer()
    
    # Analyze source files
    report = analyzer.analyze_files(['src/main.c'])
    
    # Output results
    print(f"Found {len(report.violations)} violations")
    report.to_json_file('analysis_report.json')

Command-line usage:
    python -m static_analyzer.cli analyze --path src --output report.json
"""

__version__ = "1.0.0"
__author__ = "Static Analyzer Team"
__email__ = "dev@staticanalyzer.com"
__license__ = "MIT"

import os
import fnmatch
from pathlib import Path
from typing import List, Optional, Dict, Any
from .ast import ASTParser
from .rules import RuleEngine
from .models import AnalysisReport, Violation, Standard, Severity, Confidence, RuleMetadata, SourceLocation, Deviation
from .config import AnalyzerConfig, DeviationManager, create_default_config_file
from .ai_assistant import create_ai_assistant


class StaticAnalyzer:
    """Main static analyzer class."""
    
    def __init__(self, 
                 config: Optional[AnalyzerConfig] = None,
                 deviations_file: Optional[str] = None):
        """Initialize static analyzer.
        
        Args:
            config: Analyzer configuration
            deviations_file: Path to deviations file
        """
        self.config = config or AnalyzerConfig.create_default()
        self.deviation_manager = DeviationManager(deviations_file)
        
        # Initialize components
        self.ast_parser = ASTParser(self.config.get_include_paths())
        self.rule_engine = RuleEngine()
        self.rule_engine.register_builtin_rules()
        
        # Initialize AI assistant if enabled
        self.ai_assistant = None
        if self.config.is_ai_enabled():
            self.ai_assistant = create_ai_assistant(self.config.get_ai_config())
    
    def analyze_files(self, 
                     file_paths: List[str],
                     enabled_rules: Optional[List[str]] = None) -> AnalysisReport:
        """Analyze a list of source files.
        
        Args:
            file_paths: List of C/C++ source files to analyze
            enabled_rules: Optional list of rule IDs to run
            
        Returns:
            AnalysisReport containing all violations found
        """
        if enabled_rules is None:
            enabled_rules = self.config.get_enabled_rules()
        
        # Filter out disabled rules
        disabled_rules = set(self.config.get_disabled_rules())
        enabled_rules = [rule_id for rule_id in enabled_rules 
                        if rule_id not in disabled_rules]
        
        report = AnalysisReport([], {}, {})
        
        # Filter files based on include/exclude patterns
        filtered_files = self._filter_files(file_paths)
        
        for file_path in filtered_files:
            try:
                file_violations = self._analyze_single_file(file_path, enabled_rules)
                
                # Apply deviations
                filtered_violations = self._apply_deviations(file_violations)
                
                report.violations.extend(filtered_violations)
                
            except Exception as e:
                print(f"Error analyzing {file_path}: {str(e)}")
                continue
        
        # Enhance with AI if enabled
        if self.ai_assistant:
            report.violations = self.ai_assistant.enhance_violations(report.violations)
        
        # Generate report metadata
        report.metadata = {
            "analyzer_version": "1.0.0",
            "config": {
                "enabled_rules": enabled_rules,
                "standards": [s.value for s in self.config.get_enabled_standards()],
                "ai_enabled": self.config.is_ai_enabled()
            },
            "files_analyzed": len(filtered_files),
            "total_files_provided": len(file_paths),
            "deviations_applied": len(self.deviation_manager.deviations)
        }
        
        return report
    
    def analyze_directory(self, 
                         directory_path: str,
                         recursive: bool = True,
                         file_extensions: Optional[List[str]] = None) -> AnalysisReport:
        """Analyze all C/C++ files in a directory.
        
        Args:
            directory_path: Directory to analyze
            recursive: Whether to analyze subdirectories
            file_extensions: File extensions to include
            
        Returns:
            AnalysisReport containing all violations found
        """
        if file_extensions is None:
            file_extensions = ['.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hh', '.hxx']
        
        directory = Path(directory_path)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        # Find all source files
        source_files = []
        
        if recursive:
            for ext in file_extensions:
                pattern = f"**/*{ext}"
                files = list(directory.rglob(pattern))
                source_files.extend([str(f) for f in files])
        else:
            for ext in file_extensions:
                pattern = f"*{ext}"
                files = list(directory.glob(pattern))
                source_files.extend([str(f) for f in files])
        
        return self.analyze_files(source_files)
    
    def _analyze_single_file(self, 
                           file_path: str, 
                           enabled_rules: List[str]) -> List[Violation]:
        """Analyze a single source file.
        
        Args:
            file_path: Path to source file
            enabled_rules: List of rule IDs to run
            
        Returns:
            List of violations found in the file
        """
        # Parse the file
        translation_unit = self.ast_parser.parse_file(file_path)
        if translation_unit is None:
            print(f"Warning: Failed to parse {file_path}")
            return []
        
        # Run static analysis
        violations = self.rule_engine.analyze_translation_unit(
            translation_unit, enabled_rules
        )
        
        return violations
    
    def _filter_files(self, file_paths: List[str]) -> List[str]:
        """Filter files based on include/exclude patterns.
        
        Args:
            file_paths: List of file paths to filter
            
        Returns:
            Filtered list of file paths
        """
        exclude_patterns = self.config.get_exclude_paths()
        
        filtered_files = []
        for file_path in file_paths:
            # Check if file should be excluded
            should_exclude = False
            for pattern in exclude_patterns:
                if fnmatch.fnmatch(file_path, pattern):
                    should_exclude = True
                    break
            
            if not should_exclude:
                filtered_files.append(file_path)
        
        return filtered_files
    
    def _apply_deviations(self, violations: List[Violation]) -> List[Violation]:
        """Apply deviations to filter out suppressed violations.
        
        Args:
            violations: List of violations to filter
            
        Returns:
            List of violations after applying deviations
        """
        filtered_violations = []
        
        for violation in violations:
            is_suppressed, deviation = self.deviation_manager.is_violation_suppressed(violation)
            
            if not is_suppressed:
                filtered_violations.append(violation)
            else:
                # Add deviation info to metadata
                if violation.metadata is None:
                    violation.metadata = {}
                violation.metadata["suppressed_by_deviation"] = {
                    "rule_id": deviation.rule_id,
                    "justification": deviation.justification,
                    "approved_by": deviation.approved_by
                }
        
        return filtered_violations
    
    def get_available_rules(self) -> List[Dict[str, Any]]:
        """Get information about all available rules.
        
        Returns:
            List of rule information dictionaries
        """
        return self.rule_engine.get_available_rules()
    
    def validate_config(self) -> List[str]:
        """Validate the current configuration.
        
        Returns:
            List of validation warnings/errors
        """
        issues = []
        
        # Check enabled rules exist
        enabled_rules = self.config.get_enabled_rules()
        available_rules = set(self.rule_engine.registry.list_rule_ids())
        
        for rule_id in enabled_rules:
            if rule_id not in available_rules:
                issues.append(f"Unknown rule ID: {rule_id}")
        
        # Check include paths exist
        for include_path in self.config.get_include_paths():
            if not os.path.exists(include_path):
                issues.append(f"Include path not found: {include_path}")
        
        # Check AI configuration if enabled
        if self.config.is_ai_enabled():
            ai_config = self.config.get_ai_config()
            api_key_env = ai_config.get("api_key_env", "OPENAI_API_KEY")
            if not os.getenv(api_key_env):
                issues.append(f"AI enabled but {api_key_env} environment variable not set")
        
        return issues


def create_analyzer_from_config_file(config_file: str, 
                                   deviations_file: Optional[str] = None) -> StaticAnalyzer:
    """Create analyzer from configuration file.
    
    Args:
        config_file: Path to configuration YAML file
        deviations_file: Optional path to deviations file
        
    Returns:
        StaticAnalyzer instance
    """
    config = AnalyzerConfig.from_file(config_file)
    return StaticAnalyzer(config, deviations_file)


def create_default_analyzer() -> 'StaticAnalyzer':
    """Create analyzer with default configuration.
    
    Returns:
        StaticAnalyzer instance with defaults
    """
    return StaticAnalyzer()


# Make key classes available at package level
__all__ = [
    # Core classes
    'StaticAnalyzer',
    'AnalyzerConfig', 
    'DeviationManager',
    
    # Data models
    'Violation',
    'AnalysisReport',
    'RuleMetadata', 
    'SourceLocation',
    'Deviation',
    
    # Enums
    'Standard',
    'Severity', 
    'Confidence',
    
    # Factory functions
    'create_analyzer_from_config_file',
    'create_default_analyzer',
    'create_default_config_file',
    
    # Version info
    '__version__'
]
