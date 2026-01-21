"""CERT C/C++ rule implementations."""

from typing import List, Optional
from clang.cindex import Cursor, CursorKind, TranslationUnit, TypeKind
from ..models import Violation, RuleMetadata, Standard, Severity, Confidence
from ..ast import ASTTraverser, TypeAnalyzer
from . import Rule


class CERT_EXP34_C(Rule):
    """CERT EXP34-C - Do not dereference null pointers."""
    
    def get_metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="CERT-EXP34-C",
            standard=Standard.CERT,
            title="Do not dereference null pointers",
            description="Dereferencing null pointers results in undefined behavior and can lead to program crashes or security vulnerabilities.",
            rationale="Null pointer dereferences are a common source of runtime errors and security exploits.",
            severity=Severity.CRITICAL,
            category="Memory Safety",
            references=[
                "SEI CERT C Coding Standard EXP34-C",
                "CWE-476: NULL Pointer Dereference"
            ]
        )
    
    def check_translation_unit(self, translation_unit: TranslationUnit) -> List[Violation]:
        violations = []
        
        # Find all pointer dereferences and check for potential null dereference
        for cursor in ASTTraverser.walk_ast(translation_unit.cursor):
            if cursor.kind == CursorKind.UNARY_OPERATOR:
                violations.extend(self._check_unary_dereference(cursor))
            elif cursor.kind == CursorKind.MEMBER_REF_EXPR:
                violations.extend(self._check_member_access(cursor))
            elif cursor.kind == CursorKind.ARRAY_SUBSCRIPT_EXPR:
                violations.extend(self._check_array_subscript(cursor))
        
        return violations
    
    def _check_unary_dereference(self, cursor: Cursor) -> List[Violation]:
        """Check unary dereference operations for null pointer access."""
        violations = []
        
        children = list(cursor.get_children())
        if len(children) < 1:
            return violations
        
        operand = children[0]
        
        # Check if this is a dereference operation on a pointer
        if TypeAnalyzer.is_pointer_type(operand):
            null_check_result = self._analyze_null_pointer_risk(operand)
            if null_check_result["risk_level"] != "safe":
                violations.append(
                    self.create_violation(
                        cursor,
                        f"Potential null pointer dereference: {null_check_result['reason']}",
                        metadata={
                            "risk_level": null_check_result["risk_level"],
                            "pointer_name": operand.spelling,
                            "analysis": null_check_result
                        }
                    )
                )
        
        return violations
    
    def _check_member_access(self, cursor: Cursor) -> List[Violation]:
        """Check member access operations (ptr->member) for null pointer access."""
        violations = []
        
        children = list(cursor.get_children())
        if len(children) < 1:
            return violations
        
        base_expr = children[0]
        
        # Check if base expression is a pointer that could be null
        if TypeAnalyzer.is_pointer_type(base_expr):
            null_check_result = self._analyze_null_pointer_risk(base_expr)
            if null_check_result["risk_level"] != "safe":
                violations.append(
                    self.create_violation(
                        cursor,
                        f"Potential null pointer dereference in member access: {null_check_result['reason']}",
                        metadata={
                            "risk_level": null_check_result["risk_level"],
                            "pointer_name": base_expr.spelling,
                            "member_name": cursor.spelling,
                            "analysis": null_check_result
                        }
                    )
                )
        
        return violations
    
    def _check_array_subscript(self, cursor: Cursor) -> List[Violation]:
        """Check array subscript operations for null pointer access."""
        violations = []
        
        children = list(cursor.get_children())
        if len(children) < 2:
            return violations
        
        array_expr = children[0]
        
        # Array subscript on pointer
        if TypeAnalyzer.is_pointer_type(array_expr):
            null_check_result = self._analyze_null_pointer_risk(array_expr)
            if null_check_result["risk_level"] != "safe":
                violations.append(
                    self.create_violation(
                        cursor,
                        f"Potential null pointer dereference in array subscript: {null_check_result['reason']}",
                        metadata={
                            "risk_level": null_check_result["risk_level"],
                            "pointer_name": array_expr.spelling,
                            "analysis": null_check_result
                        }
                    )
                )
        
        return violations
    
    def _analyze_null_pointer_risk(self, cursor: Cursor) -> dict:
        """Analyze the risk of null pointer dereference for a given cursor."""
        # This is a simplified analysis - a production version would be much more sophisticated
        
        if cursor.kind == CursorKind.DECL_REF_EXPR:
            var_name = cursor.spelling
            
            # Check for obvious null assignments
            if self._has_null_assignment(cursor, var_name):
                return {
                    "risk_level": "high",
                    "reason": f"Variable '{var_name}' may have been assigned NULL",
                    "confidence": "medium"
                }
            
            # Check for lack of null check before use
            if not self._has_null_check_before_use(cursor, var_name):
                return {
                    "risk_level": "medium", 
                    "reason": f"Variable '{var_name}' used without null check",
                    "confidence": "low"
                }
        
        # Check for function calls that might return null
        elif cursor.kind == CursorKind.CALL_EXPR:
            func_name = cursor.spelling
            if func_name in ["malloc", "calloc", "realloc", "fopen", "strchr", "strstr"]:
                return {
                    "risk_level": "high",
                    "reason": f"Function '{func_name}' may return NULL",
                    "confidence": "high"
                }
        
        return {
            "risk_level": "safe",
            "reason": "No obvious null pointer risk detected",
            "confidence": "low"
        }
    
    def _has_null_assignment(self, cursor: Cursor, var_name: str) -> bool:
        """Check if variable has been assigned NULL in the current scope."""
        # Simplified check - look for NULL assignments in the same function
        parent_func = ASTTraverser.get_parent_function(cursor)
        if not parent_func:
            return False
        
        for node in ASTTraverser.walk_ast(parent_func):
            if (node.kind == CursorKind.BINARY_OPERATOR and 
                self._is_assignment_to_var(node, var_name) and
                self._assigns_null_value(node)):
                return True
        
        return False
    
    def _has_null_check_before_use(self, cursor: Cursor, var_name: str) -> bool:
        """Check if there's a null check before this usage."""
        # This is a very simplified implementation
        # A real implementation would need control flow analysis
        
        parent_func = ASTTraverser.get_parent_function(cursor)
        if not parent_func:
            return False
        
        # Look for if statements that check the variable
        for node in ASTTraverser.walk_ast(parent_func):
            if (node.kind == CursorKind.IF_STMT and 
                self._checks_null_condition(node, var_name)):
                return True
        
        return False
    
    def _is_assignment_to_var(self, cursor: Cursor, var_name: str) -> bool:
        """Check if cursor is an assignment to the specified variable."""
        children = list(cursor.get_children())
        if len(children) >= 1:
            left_operand = children[0]
            return (left_operand.kind == CursorKind.DECL_REF_EXPR and 
                   left_operand.spelling == var_name)
        return False
    
    def _assigns_null_value(self, cursor: Cursor) -> bool:
        """Check if assignment assigns a NULL value."""
        # Look for NULL literal or 0 in pointer context
        for child in cursor.get_children():
            if (child.kind == CursorKind.INTEGER_LITERAL or
                child.kind == CursorKind.GNU_NULL_EXPR or
                (child.kind == CursorKind.DECL_REF_EXPR and 
                 child.spelling.upper() == "NULL")):
                return True
        return False
    
    def _checks_null_condition(self, if_cursor: Cursor, var_name: str) -> bool:
        """Check if IF statement condition checks for null."""
        # Very simplified - look for variable reference in condition
        children = list(if_cursor.get_children())
        if len(children) >= 1:
            condition = children[0]
            for node in ASTTraverser.walk_ast(condition):
                if (node.kind == CursorKind.DECL_REF_EXPR and 
                    node.spelling == var_name):
                    return True
        return False


class CERT_ARR30_C(Rule):
    """CERT ARR30-C - Do not form or use out-of-bounds pointers or array subscripts."""
    
    def get_metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="CERT-ARR30-C",
            standard=Standard.CERT,
            title="Do not form or use out-of-bounds pointers or array subscripts",
            description="Forming or using out-of-bounds pointers or array subscripts results in undefined behavior.",
            rationale="Buffer overflows are a major source of security vulnerabilities and program crashes.",
            severity=Severity.CRITICAL,
            category="Memory Safety",
            references=[
                "SEI CERT C Coding Standard ARR30-C",
                "CWE-125: Out-of-bounds Read",
                "CWE-787: Out-of-bounds Write"
            ]
        )
    
    def check_translation_unit(self, translation_unit: TranslationUnit) -> List[Violation]:
        violations = []
        
        # Find array subscript expressions and check bounds
        for cursor in ASTTraverser.walk_ast(translation_unit.cursor):
            if cursor.kind == CursorKind.ARRAY_SUBSCRIPT_EXPR:
                violations.extend(self._check_array_bounds(cursor))
            elif cursor.kind == CursorKind.BINARY_OPERATOR:
                # Check pointer arithmetic
                violations.extend(self._check_pointer_arithmetic(cursor))
        
        return violations
    
    def _check_array_bounds(self, cursor: Cursor) -> List[Violation]:
        """Check array subscript for potential bounds violations."""
        violations = []
        
        children = list(cursor.get_children())
        if len(children) < 2:
            return violations
        
        array_expr = children[0]
        index_expr = children[1]
        
        # Try to get array size and index value
        array_size = self._get_array_size(array_expr)
        index_value = self._get_constant_value(index_expr)
        
        if array_size is not None and index_value is not None:
            if index_value < 0 or index_value >= array_size:
                violations.append(
                    self.create_violation(
                        cursor,
                        f"Array index {index_value} is out of bounds for array of size {array_size}",
                        metadata={
                            "array_size": array_size,
                            "index_value": index_value,
                            "array_name": array_expr.spelling if array_expr.spelling else "unknown"
                        }
                    )
                )
        elif array_size is not None:
            # Can't determine index value, but check for suspicious patterns
            if self._is_suspicious_index(index_expr):
                violations.append(
                    self.create_violation(
                        cursor,
                        f"Potentially unsafe array access - index may be out of bounds",
                        metadata={
                            "array_size": array_size,
                            "array_name": array_expr.spelling if array_expr.spelling else "unknown",
                            "index_expression": "dynamic"
                        }
                    )
                )
        
        return violations
    
    def _check_pointer_arithmetic(self, cursor: Cursor) -> List[Violation]:
        """Check pointer arithmetic for potential out-of-bounds access."""
        violations = []
        
        children = list(cursor.get_children())
        if len(children) < 2:
            return violations
        
        left_operand = children[0]
        right_operand = children[1]
        
        # Check for pointer + large offset
        if (TypeAnalyzer.is_pointer_type(left_operand) and 
            TypeAnalyzer.is_integer_type(right_operand)):
            
            offset_value = self._get_constant_value(right_operand)
            if offset_value is not None and offset_value > 1000:  # Arbitrary large threshold
                violations.append(
                    self.create_violation(
                        cursor,
                        f"Large pointer offset ({offset_value}) may cause out-of-bounds access",
                        metadata={
                            "offset_value": offset_value,
                            "pointer_name": left_operand.spelling if left_operand.spelling else "unknown"
                        }
                    )
                )
        
        return violations
    
    def _get_array_size(self, cursor: Cursor) -> Optional[int]:
        """Try to determine the size of an array."""
        if cursor.kind == CursorKind.DECL_REF_EXPR:
            # Look for the variable declaration
            decl = cursor.get_definition() or cursor.referenced
            if decl and decl.kind == CursorKind.VAR_DECL:
                array_type = decl.type
                if array_type.kind == TypeKind.CONSTANTARRAY:
                    return array_type.get_array_size()
        
        return None
    
    def _get_constant_value(self, cursor: Cursor) -> Optional[int]:
        """Try to get constant integer value from cursor."""
        if cursor.kind == CursorKind.INTEGER_LITERAL:
            # This is simplified - would need token analysis for actual value
            try:
                # Try to get the value from tokens
                tokens = list(cursor.get_tokens())
                if tokens:
                    return int(tokens[0].spelling)
            except (ValueError, IndexError):
                pass
        
        return None
    
    def _is_suspicious_index(self, cursor: Cursor) -> bool:
        """Check if index expression looks suspicious."""
        # Look for potentially problematic patterns
        if cursor.kind == CursorKind.BINARY_OPERATOR:
            # Unchecked arithmetic operations
            return True
        elif cursor.kind == CursorKind.CALL_EXPR:
            # Function calls that might return large values
            return True
        
        return False
