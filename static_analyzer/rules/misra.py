"""MISRA C:2012 rule implementations."""

from typing import List, Set
from clang.cindex import Cursor, CursorKind, TranslationUnit, TypeKind
from ..models import Violation, RuleMetadata, Standard, Severity, Confidence
from ..ast import ASTTraverser, TypeAnalyzer
from . import Rule


class MISRA_C_2012_8_7(Rule):
    """MISRA C:2012 Rule 8.7 - Objects should be defined at block scope if they are only accessed from within a single function."""
    
    def get_metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="MISRA-C-2012-8.7",
            standard=Standard.MISRA,
            title="Objects should be defined at block scope",
            description="Objects should be defined at block scope if they are only accessed from within a single function.",
            rationale="Defining objects at the smallest possible scope improves code clarity and reduces the risk of unintended access.",
            severity=Severity.MINOR,
            category="Scope",
            references=[
                "MISRA C:2012 Rule 8.7",
                "ISO/IEC 9899:2011 Section 6.2.1"
            ]
        )
    
    def check_translation_unit(self, translation_unit: TranslationUnit) -> List[Violation]:
        violations = []
        
        # Find all global variable declarations
        global_vars = []
        for cursor in ASTTraverser.walk_ast(translation_unit.cursor):
            if (cursor.kind == CursorKind.VAR_DECL and 
                cursor.semantic_parent.kind == CursorKind.TRANSLATION_UNIT):
                global_vars.append(cursor)
        
        # For each global variable, check if it's only used in one function
        for var_cursor in global_vars:
            if self._is_static_variable(var_cursor):
                continue  # Static variables are okay at file scope
            
            usage_functions = self._find_variable_usage_functions(
                translation_unit.cursor, var_cursor.spelling
            )
            
            if len(usage_functions) == 1:
                # Variable is only used in one function - should be local
                violations.append(
                    self.create_violation(
                        var_cursor,
                        f"Variable '{var_cursor.spelling}' is only used in function "
                        f"'{usage_functions[0]}' and should be defined at block scope",
                        metadata={
                            "variable_name": var_cursor.spelling,
                            "used_in_function": usage_functions[0]
                        }
                    )
                )
        
        return violations
    
    def _is_static_variable(self, cursor: Cursor) -> bool:
        """Check if variable has static storage class."""
        return cursor.storage_class == 1  # Static storage class
    
    def _find_variable_usage_functions(self, root: Cursor, var_name: str) -> Set[str]:
        """Find all functions that use a specific variable."""
        usage_functions = set()
        
        for cursor in ASTTraverser.walk_ast(root):
            if (cursor.kind == CursorKind.DECL_REF_EXPR and 
                cursor.spelling == var_name):
                # Find the parent function
                parent_func = ASTTraverser.get_parent_function(cursor)
                if parent_func:
                    usage_functions.add(parent_func.spelling)
        
        return usage_functions


class MISRA_C_2012_10_1(Rule):
    """MISRA C:2012 Rule 10.1 - Operands shall not be of an inappropriate essential type."""
    
    def get_metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="MISRA-C-2012-10.1",
            standard=Standard.MISRA,
            title="Operands shall not be of inappropriate essential type",
            description="Operands shall not be of an inappropriate essential type for the operator.",
            rationale="Using inappropriate types can lead to unexpected behavior and potential security vulnerabilities.",
            severity=Severity.MAJOR,
            category="Type Safety",
            references=[
                "MISRA C:2012 Rule 10.1",
                "ISO/IEC 9899:2011 Section 6.3"
            ]
        )
    
    def check_translation_unit(self, translation_unit: TranslationUnit) -> List[Violation]:
        violations = []
        
        # Find all binary operators and check operand types
        for cursor in ASTTraverser.walk_ast(translation_unit.cursor):
            if cursor.kind == CursorKind.BINARY_OPERATOR:
                violations.extend(self._check_binary_operator(cursor))
            elif cursor.kind == CursorKind.UNARY_OPERATOR:
                violations.extend(self._check_unary_operator(cursor))
        
        return violations
    
    def _check_binary_operator(self, cursor: Cursor) -> List[Violation]:
        """Check binary operator for type compatibility."""
        violations = []
        
        children = list(cursor.get_children())
        if len(children) < 2:
            return violations
        
        left_operand = children[0]
        right_operand = children[1]
        
        # Check for mixing signed/unsigned integers
        if (TypeAnalyzer.is_integer_type(left_operand) and 
            TypeAnalyzer.is_integer_type(right_operand)):
            
            left_type = left_operand.type
            right_type = right_operand.type
            
            # Check if one is signed and the other unsigned
            if self._is_signed_unsigned_mismatch(left_type, right_type):
                violations.append(
                    self.create_violation(
                        cursor,
                        f"Mixed signed/unsigned operands in binary operation: "
                        f"{left_type.spelling} and {right_type.spelling}",
                        metadata={
                            "left_type": left_type.spelling,
                            "right_type": right_type.spelling,
                            "operator": self._get_operator_spelling(cursor)
                        }
                    )
                )
        
        # Check for pointer arithmetic on non-integer types
        if (TypeAnalyzer.is_pointer_type(left_operand) and 
            not TypeAnalyzer.is_integer_type(right_operand) and
            not TypeAnalyzer.is_pointer_type(right_operand)):
            
            violations.append(
                self.create_violation(
                    cursor,
                    f"Inappropriate pointer arithmetic with non-integer type: {right_operand.type.spelling}",
                    metadata={
                        "pointer_type": left_operand.type.spelling,
                        "operand_type": right_operand.type.spelling
                    }
                )
            )
        
        return violations
    
    def _check_unary_operator(self, cursor: Cursor) -> List[Violation]:
        """Check unary operator for type appropriateness."""
        violations = []
        
        children = list(cursor.get_children())
        if len(children) < 1:
            return violations
        
        operand = children[0]
        
        # Check logical NOT on non-boolean types (simplified check)
        if (self._is_logical_not_operator(cursor) and 
            not self._is_boolean_context_appropriate(operand)):
            
            violations.append(
                self.create_violation(
                    cursor,
                    f"Logical NOT operator applied to potentially inappropriate type: {operand.type.spelling}",
                    metadata={
                        "operand_type": operand.type.spelling
                    }
                )
            )
        
        return violations
    
    def _is_signed_unsigned_mismatch(self, type1, type2) -> bool:
        """Check if types represent signed/unsigned mismatch."""
        signed_types = [TypeKind.CHAR_S, TypeKind.SCHAR, TypeKind.SHORT, 
                       TypeKind.INT, TypeKind.LONG, TypeKind.LONGLONG]
        unsigned_types = [TypeKind.CHAR_U, TypeKind.UCHAR, TypeKind.USHORT, 
                         TypeKind.UINT, TypeKind.ULONG, TypeKind.ULONGLONG]
        
        type1_signed = type1.kind in signed_types
        type1_unsigned = type1.kind in unsigned_types
        type2_signed = type2.kind in signed_types
        type2_unsigned = type2.kind in unsigned_types
        
        return (type1_signed and type2_unsigned) or (type1_unsigned and type2_signed)
    
    def _get_operator_spelling(self, cursor: Cursor) -> str:
        """Get string representation of operator (simplified)."""
        # This is a simplified implementation
        # In a real implementation, you'd need to parse the tokens
        return "binary_op"
    
    def _is_logical_not_operator(self, cursor: Cursor) -> bool:
        """Check if cursor represents logical NOT operator."""
        # Simplified check - would need token analysis for precision
        return cursor.kind == CursorKind.UNARY_OPERATOR
    
    def _is_boolean_context_appropriate(self, cursor: Cursor) -> bool:
        """Check if operand is appropriate for boolean context."""
        # Simplified check - integer types and pointers are generally okay
        return (TypeAnalyzer.is_integer_type(cursor) or 
                TypeAnalyzer.is_pointer_type(cursor) or
                cursor.type.kind == TypeKind.BOOL)


class MISRA_C_2012_16_4(Rule):
    """MISRA C:2012 Rule 16.4 - Every switch statement shall have a default label."""
    
    def get_metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="MISRA-C-2012-16.4",
            standard=Standard.MISRA,
            title="Every switch statement shall have a default label",
            description="Every switch statement shall have a default label to handle unexpected values.",
            rationale="A default label ensures that all possible values are handled, improving robustness.",
            severity=Severity.MAJOR,
            category="Control Flow",
            references=[
                "MISRA C:2012 Rule 16.4",
                "ISO/IEC 9899:2011 Section 6.8.4.2"
            ]
        )
    
    def check_translation_unit(self, translation_unit: TranslationUnit) -> List[Violation]:
        violations = []
        
        # Find all switch statements
        for cursor in ASTTraverser.walk_ast(translation_unit.cursor):
            if cursor.kind == CursorKind.SWITCH_STMT:
                if not self._has_default_label(cursor):
                    violations.append(
                        self.create_violation(
                            cursor,
                            "Switch statement missing default label"
                        )
                    )
        
        return violations
    
    def _has_default_label(self, switch_cursor: Cursor) -> bool:
        """Check if switch statement has a default label."""
        for child in switch_cursor.get_children():
            if child.kind == CursorKind.DEFAULT_STMT:
                return True
            # Recursively check compound statements
            if child.kind == CursorKind.COMPOUND_STMT:
                for grandchild in ASTTraverser.walk_ast(child):
                    if grandchild.kind == CursorKind.DEFAULT_STMT:
                        return True
        return False
