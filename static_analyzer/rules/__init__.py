"""Rule engine for static analysis."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Type
from clang.cindex import Cursor, TranslationUnit
from ..models import Violation, RuleMetadata, SourceLocation, Confidence


class Rule(ABC):
    """Abstract base class for static analysis rules."""
    
    def __init__(self):
        """Initialize the rule."""
        self._metadata: Optional[RuleMetadata] = None
    
    @property
    def metadata(self) -> RuleMetadata:
        """Get rule metadata."""
        if self._metadata is None:
            self._metadata = self.get_metadata()
        return self._metadata
    
    @abstractmethod
    def get_metadata(self) -> RuleMetadata:
        """Return metadata for this rule.
        
        Returns:
            RuleMetadata object containing rule information
        """
        pass
    
    @abstractmethod
    def check_translation_unit(self, translation_unit: TranslationUnit) -> List[Violation]:
        """Check a translation unit for violations.
        
        Args:
            translation_unit: Clang translation unit to analyze
            
        Returns:
            List of violations found
        """
        pass
    
    def check_cursor(self, cursor: Cursor) -> List[Violation]:
        """Check a specific cursor for violations.
        
        Args:
            cursor: AST cursor to check
            
        Returns:
            List of violations found
        """
        # Default implementation - override if needed
        return []
    
    def create_violation(self, 
                        cursor: Cursor, 
                        message: str,
                        source_context: Optional[str] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> Violation:
        """Create a violation for this rule.
        
        Args:
            cursor: AST cursor where violation occurred
            message: Violation message
            source_context: Source code context
            metadata: Additional metadata
            
        Returns:
            Violation object
        """
        from ..ast import SourceLocationExtractor
        
        location = SourceLocationExtractor.from_clang_location(cursor.location)
        
        if source_context is None:
            source_context = SourceLocationExtractor.get_source_text(cursor)
        
        return Violation(
            rule_id=self.metadata.id,
            standard=self.metadata.standard,
            location=location,
            message=message,
            severity=self.metadata.severity,
            confidence=Confidence.MEDIUM,  # Default confidence
            source_context=source_context,
            metadata=metadata
        )


class RuleRegistry:
    """Registry for managing static analysis rules."""
    
    def __init__(self):
        """Initialize the rule registry."""
        self._rules: Dict[str, Type[Rule]] = {}
        self._instances: Dict[str, Rule] = {}
    
    def register_rule(self, rule_class: Type[Rule]) -> None:
        """Register a rule class.
        
        Args:
            rule_class: Rule class to register
        """
        # Create instance to get metadata
        instance = rule_class()
        rule_id = instance.metadata.id
        
        self._rules[rule_id] = rule_class
        self._instances[rule_id] = instance
    
    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Get a rule instance by ID.
        
        Args:
            rule_id: Rule identifier
            
        Returns:
            Rule instance or None if not found
        """
        return self._instances.get(rule_id)
    
    def get_all_rules(self) -> List[Rule]:
        """Get all registered rule instances.
        
        Returns:
            List of all rule instances
        """
        return list(self._instances.values())
    
    def get_enabled_rules(self, enabled_rule_ids: List[str]) -> List[Rule]:
        """Get enabled rule instances.
        
        Args:
            enabled_rule_ids: List of rule IDs to include
            
        Returns:
            List of enabled rule instances
        """
        enabled_rules = []
        for rule_id in enabled_rule_ids:
            rule = self.get_rule(rule_id)
            if rule:
                enabled_rules.append(rule)
        return enabled_rules
    
    def get_rules_by_standard(self, standard: str) -> List[Rule]:
        """Get all rules for a specific standard.
        
        Args:
            standard: Standard name (e.g., "MISRA", "CERT")
            
        Returns:
            List of matching rules
        """
        return [
            rule for rule in self._instances.values()
            if rule.metadata.standard.value == standard
        ]
    
    def list_rule_ids(self) -> List[str]:
        """Get list of all registered rule IDs.
        
        Returns:
            List of rule IDs
        """
        return list(self._rules.keys())


class RuleEngine:
    """Engine for executing static analysis rules."""
    
    def __init__(self, registry: Optional[RuleRegistry] = None):
        """Initialize the rule engine.
        
        Args:
            registry: Rule registry to use
        """
        self.registry = registry or RuleRegistry()
    
    def analyze_translation_unit(self, 
                                translation_unit: TranslationUnit,
                                enabled_rules: Optional[List[str]] = None) -> List[Violation]:
        """Analyze a translation unit with specified rules.
        
        Args:
            translation_unit: Translation unit to analyze
            enabled_rules: List of rule IDs to run, or None for all rules
            
        Returns:
            List of violations found
        """
        if enabled_rules is None:
            rules = self.registry.get_all_rules()
        else:
            rules = self.registry.get_enabled_rules(enabled_rules)
        
        violations = []
        
        for rule in rules:
            try:
                rule_violations = rule.check_translation_unit(translation_unit)
                violations.extend(rule_violations)
            except Exception as e:
                print(f"Error running rule {rule.metadata.id}: {str(e)}")
                continue
        
        return violations
    
    def register_builtin_rules(self) -> None:
        """Register all built-in rules."""
        try:
            from .misra import MISRA_C_2012_8_7, MISRA_C_2012_10_1
            from .cert import CERT_EXP34_C
            
            self.registry.register_rule(MISRA_C_2012_8_7)
            self.registry.register_rule(MISRA_C_2012_10_1) 
            self.registry.register_rule(CERT_EXP34_C)
        except ImportError as e:
            print(f"Warning: Could not import built-in rules: {e}")
            print("This may be due to missing libclang dependency")
    
    def get_available_rules(self) -> List[Dict[str, Any]]:
        """Get information about all available rules.
        
        Returns:
            List of rule information dictionaries
        """
        rules_info = []
        for rule in self.registry.get_all_rules():
            metadata = rule.metadata
            rules_info.append({
                "id": metadata.id,
                "standard": metadata.standard.value,
                "title": metadata.title,
                "description": metadata.description,
                "severity": metadata.severity.value,
                "category": metadata.category
            })
        return rules_info
