"""AST utilities for parsing C/C++ source code using libclang."""

from typing import Optional, List, Iterator, Tuple, Any
import os
from pathlib import Path
from clang.cindex import (
    Index, 
    TranslationUnit, 
    Cursor, 
    CursorKind, 
    TypeKind,
    SourceLocation as ClangSourceLocation,
    SourceRange
)
from ..models import SourceLocation


class ASTParser:
    """Clang AST parser for C/C++ source files."""
    
    def __init__(self, include_paths: Optional[List[str]] = None):
        """Initialize the AST parser.
        
        Args:
            include_paths: Additional include directories for compilation
        """
        self.index = Index.create()
        self.include_paths = include_paths or []
        
    def parse_file(self, file_path: str, 
                   additional_args: Optional[List[str]] = None) -> Optional[TranslationUnit]:
        """Parse a C/C++ source file and return the translation unit.
        
        Args:
            file_path: Path to the source file
            additional_args: Additional clang arguments
            
        Returns:
            TranslationUnit if parsing succeeds, None otherwise
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Source file not found: {file_path}")
            
        args = []
        
        # Add include paths
        for include_path in self.include_paths:
            args.extend(['-I', include_path])
            
        # Add standard arguments for embedded C
        args.extend([
            '-std=c99',
            '-Wall',
            '-Wextra',
            '-fno-builtin',
            '-nostdlib'
        ])
        
        # Add any additional arguments
        if additional_args:
            args.extend(additional_args)
            
        try:
            translation_unit = self.index.parse(
                file_path,
                args=args,
                options=TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD
            )
            
            # Check for parsing errors
            if translation_unit is None:
                return None
                
            diagnostics = list(translation_unit.diagnostics)
            severe_errors = [d for d in diagnostics if d.severity >= 3]  # Error or Fatal
            
            if severe_errors:
                print(f"Warning: {len(severe_errors)} parsing errors in {file_path}")
                for diag in severe_errors[:5]:  # Show first 5 errors
                    print(f"  {diag.location.file}:{diag.location.line}: {diag.spelling}")
                    
            return translation_unit
            
        except Exception as e:
            print(f"Failed to parse {file_path}: {str(e)}")
            return None


class ASTTraverser:
    """Utility class for traversing Clang AST nodes."""
    
    @staticmethod
    def walk_ast(cursor: Cursor, max_depth: Optional[int] = None) -> Iterator[Cursor]:
        """Recursively walk through AST nodes.
        
        Args:
            cursor: Starting cursor
            max_depth: Maximum traversal depth
            
        Yields:
            AST cursor nodes
        """
        yield cursor
        
        if max_depth is not None and max_depth <= 0:
            return
            
        for child in cursor.get_children():
            next_depth = max_depth - 1 if max_depth is not None else None
            yield from ASTTraverser.walk_ast(child, next_depth)
    
    @staticmethod
    def find_nodes_by_kind(cursor: Cursor, kind: CursorKind) -> Iterator[Cursor]:
        """Find all nodes of a specific kind.
        
        Args:
            cursor: Starting cursor
            kind: CursorKind to search for
            
        Yields:
            Matching cursor nodes
        """
        for node in ASTTraverser.walk_ast(cursor):
            if node.kind == kind:
                yield node
    
    @staticmethod
    def find_functions(cursor: Cursor) -> Iterator[Cursor]:
        """Find all function definitions and declarations."""
        return ASTTraverser.find_nodes_by_kind(cursor, CursorKind.FUNCTION_DECL)
    
    @staticmethod
    def find_variables(cursor: Cursor) -> Iterator[Cursor]:
        """Find all variable declarations."""
        return ASTTraverser.find_nodes_by_kind(cursor, CursorKind.VAR_DECL)
    
    @staticmethod
    def find_calls(cursor: Cursor) -> Iterator[Cursor]:
        """Find all function calls."""
        return ASTTraverser.find_nodes_by_kind(cursor, CursorKind.CALL_EXPR)
    
    @staticmethod
    def get_parent_function(cursor: Cursor) -> Optional[Cursor]:
        """Get the parent function of a cursor."""
        parent = cursor.semantic_parent
        while parent:
            if parent.kind == CursorKind.FUNCTION_DECL:
                return parent
            parent = parent.semantic_parent
        return None


class SourceLocationExtractor:
    """Extract and convert source location information."""
    
    @staticmethod
    def from_clang_location(clang_loc: ClangSourceLocation) -> SourceLocation:
        """Convert Clang source location to our format.
        
        Args:
            clang_loc: Clang SourceLocation
            
        Returns:
            SourceLocation object
        """
        file_obj = clang_loc.file
        file_path = file_obj.name if file_obj else "unknown"
        
        return SourceLocation(
            file_path=file_path,
            line=clang_loc.line,
            column=clang_loc.column
        )
    
    @staticmethod
    def from_clang_range(clang_range: SourceRange) -> SourceLocation:
        """Convert Clang source range to our format.
        
        Args:
            clang_range: Clang SourceRange
            
        Returns:
            SourceLocation object with range information
        """
        start = clang_range.start
        end = clang_range.end
        
        file_obj = start.file
        file_path = file_obj.name if file_obj else "unknown"
        
        return SourceLocation(
            file_path=file_path,
            line=start.line,
            column=start.column,
            end_line=end.line,
            end_column=end.column
        )
    
    @staticmethod
    def get_source_text(cursor: Cursor) -> Optional[str]:
        """Get the source code text for a cursor.
        
        Args:
            cursor: AST cursor
            
        Returns:
            Source code text or None
        """
        try:
            extent = cursor.extent
            if not extent.start.file:
                return None
                
            file_path = extent.start.file.name
            if not os.path.exists(file_path):
                return None
                
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            start_line = extent.start.line - 1  # Convert to 0-based
            end_line = extent.end.line - 1
            start_col = extent.start.column - 1
            end_col = extent.end.column - 1
            
            if start_line == end_line:
                return lines[start_line][start_col:end_col]
            else:
                result = lines[start_line][start_col:]
                for line_idx in range(start_line + 1, end_line):
                    result += lines[line_idx]
                result += lines[end_line][:end_col]
                return result
                
        except Exception:
            return None


class TypeAnalyzer:
    """Analyze type information from AST."""
    
    @staticmethod
    def is_integer_type(cursor: Cursor) -> bool:
        """Check if cursor represents an integer type."""
        type_obj = cursor.type
        return type_obj.kind in [
            TypeKind.CHAR_S, TypeKind.CHAR_U,
            TypeKind.SCHAR, TypeKind.UCHAR,
            TypeKind.SHORT, TypeKind.USHORT,
            TypeKind.INT, TypeKind.UINT,
            TypeKind.LONG, TypeKind.ULONG,
            TypeKind.LONGLONG, TypeKind.ULONGLONG
        ]
    
    @staticmethod
    def is_floating_type(cursor: Cursor) -> bool:
        """Check if cursor represents a floating-point type."""
        type_obj = cursor.type
        return type_obj.kind in [TypeKind.FLOAT, TypeKind.DOUBLE, TypeKind.LONGDOUBLE]
    
    @staticmethod
    def is_pointer_type(cursor: Cursor) -> bool:
        """Check if cursor represents a pointer type."""
        return cursor.type.kind == TypeKind.POINTER
    
    @staticmethod
    def is_array_type(cursor: Cursor) -> bool:
        """Check if cursor represents an array type."""
        return cursor.type.kind == TypeKind.CONSTANTARRAY
    
    @staticmethod
    def get_pointee_type(cursor: Cursor) -> Optional[Any]:
        """Get the type that a pointer points to."""
        if TypeAnalyzer.is_pointer_type(cursor):
            return cursor.type.get_pointee()
        return None
    
    @staticmethod
    def get_type_size(cursor: Cursor) -> Optional[int]:
        """Get the size of a type in bytes."""
        try:
            return cursor.type.get_size()
        except:
            return None
