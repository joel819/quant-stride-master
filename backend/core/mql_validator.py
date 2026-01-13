"""
MQL5 Validator
Compiles MQL5 code using MetaEditor CLI and handles error fixing.
"""

import subprocess
import tempfile
import re
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings


class CompileErrorType(str, Enum):
    """Types of MQL5 compilation errors."""
    SYNTAX = "syntax"
    MISSING_INCLUDE = "missing_include"
    UNDEFINED_VARIABLE = "undefined_variable"
    UNDEFINED_FUNCTION = "undefined_function"
    TYPE_MISMATCH = "type_mismatch"
    MISSING_SEMICOLON = "missing_semicolon"
    UNKNOWN = "unknown"


@dataclass
class CompileError:
    """A single compilation error."""
    line: int
    column: int
    error_type: CompileErrorType
    message: str
    code: str = ""
    auto_fixable: bool = False
    fix_suggestion: Optional[str] = None


@dataclass
class CompilationResult:
    """Result of MQL5 compilation attempt."""
    success: bool
    errors: list[CompileError] = field(default_factory=list)
    warnings: list[CompileError] = field(default_factory=list)
    raw_output: str = ""
    fixed_code: Optional[str] = None
    compile_attempts: int = 0
    
    @property
    def error_count(self) -> int:
        return len(self.errors)
    
    @property
    def warning_count(self) -> int:
        return len(self.warnings)


class MQLValidator:
    """
    Validates MQL5 code by compiling with MetaEditor.
    
    Features:
    - Compile MQL5 code using MetaEditor CLI
    - Parse compiler errors and warnings
    - Auto-fix common issues
    - Retry until success or max attempts
    """
    
    # Regex patterns for error parsing
    ERROR_PATTERN = re.compile(
        r"^(.+?)\((\d+),(\d+)\)\s*:\s*(error|warning)\s+(\d+):\s*(.+)$",
        re.MULTILINE
    )
    
    # Common auto-fixable patterns
    MISSING_INCLUDE_PATTERN = re.compile(r"'(\w+\.mqh)' - file not found")
    UNDEFINED_VAR_PATTERN = re.compile(r"'(\w+)' - undeclared identifier")
    UNDEFINED_FUNC_PATTERN = re.compile(r"'(\w+)' - function not defined")
    MISSING_SEMICOLON_PATTERN = re.compile(r"';' - semicolon expected")
    
    # Standard includes that might be needed
    STANDARD_INCLUDES = {
        "Trade.mqh": "#include <Trade\\Trade.mqh>",
        "PositionInfo.mqh": "#include <Trade\\PositionInfo.mqh>",
        "OrderInfo.mqh": "#include <Trade\\OrderInfo.mqh>",
        "SymbolInfo.mqh": "#include <Trade\\SymbolInfo.mqh>",
        "AccountInfo.mqh": "#include <Trade\\AccountInfo.mqh>",
        "DealInfo.mqh": "#include <Trade\\DealInfo.mqh>",
        "HistoryPositionInfo.mqh": "#include <Trade\\HistoryPositionInfo.mqh>",
    }
    
    def __init__(self, metaeditor_path: str = None):
        self.metaeditor_path = metaeditor_path or settings.METAEDITOR_PATH
        self.compile_timeout = settings.COMPILE_TIMEOUT
        self.max_retries = settings.MAX_COMPILE_RETRIES
        self.auto_fix_enabled = settings.AUTO_FIX_ENABLED
    
    def validate(self, mql5_code: str, filename: str = "EA.mq5") -> CompilationResult:
        """
        Validate MQL5 code by attempting compilation.
        
        Args:
            mql5_code: The MQL5 source code
            filename: Name for the temporary file
            
        Returns:
            CompilationResult with success status and any errors
        """
        result = CompilationResult(success=False)
        current_code = mql5_code
        
        for attempt in range(self.max_retries):
            result.compile_attempts = attempt + 1
            
            # Compile the code
            compile_result = self._compile(current_code, filename)
            
            if compile_result.success:
                result.success = True
                result.fixed_code = current_code if current_code != mql5_code else None
                result.raw_output = compile_result.raw_output
                return result
            
            result.errors = compile_result.errors
            result.warnings = compile_result.warnings
            result.raw_output = compile_result.raw_output
            
            # Try to auto-fix if enabled
            if self.auto_fix_enabled and attempt < self.max_retries - 1:
                fixed_code = self._try_auto_fix(current_code, compile_result.errors)
                if fixed_code and fixed_code != current_code:
                    current_code = fixed_code
                    continue
            
            break
        
        return result
    
    def _compile(self, code: str, filename: str) -> CompilationResult:
        """
        Compile MQL5 code using MetaEditor CLI.
        
        Creates a temporary file and runs MetaEditor in compile mode.
        """
        result = CompilationResult(success=False)
        
        # Check if MetaEditor exists
        if not os.path.exists(self.metaeditor_path):
            # Return mock result for non-Windows systems
            result.raw_output = "MetaEditor not found - running in validation-only mode"
            result.success = self._mock_validate(code)
            return result
        
        # Create temporary directory and file
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir) / filename
            temp_file.write_text(code, encoding="utf-8")
            
            # Build command
            cmd = [
                self.metaeditor_path,
                "/compile:" + str(temp_file),
                "/log"
            ]
            
            try:
                # Run compiler
                process = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.compile_timeout,
                    cwd=temp_dir
                )
                
                result.raw_output = process.stdout + process.stderr
                
                # Check for log file
                log_file = temp_file.with_suffix(".log")
                if log_file.exists():
                    result.raw_output += "\n" + log_file.read_text(encoding="utf-8")
                
                # Parse errors and warnings
                result.errors, result.warnings = self._parse_output(result.raw_output)
                
                # Check for successful compilation (no errors)
                result.success = len(result.errors) == 0
                
                # Also check if .ex5 was created
                ex5_file = temp_file.with_suffix(".ex5")
                if ex5_file.exists():
                    result.success = True
                
            except subprocess.TimeoutExpired:
                result.raw_output = "Compilation timed out"
                result.errors.append(CompileError(
                    line=0, column=0,
                    error_type=CompileErrorType.UNKNOWN,
                    message="Compilation timed out"
                ))
            except Exception as e:
                result.raw_output = f"Compilation failed: {str(e)}"
                result.errors.append(CompileError(
                    line=0, column=0,
                    error_type=CompileErrorType.UNKNOWN,
                    message=str(e)
                ))
        
        return result
    
    def _mock_validate(self, code: str) -> bool:
        """
        Basic validation when MetaEditor is not available.
        Checks for common structural issues.
        """
        # Check for required functions
        required_functions = ["OnInit", "OnTick", "OnDeinit"]
        
        for func in required_functions:
            if func not in code:
                return False
        
        # Check for balanced braces
        if code.count("{") != code.count("}"):
            return False
        
        # Check for balanced parentheses
        if code.count("(") != code.count(")"):
            return False
        
        # Check for property declaration
        if "#property" not in code:
            return False
        
        return True
    
    def _parse_output(self, output: str) -> tuple[list[CompileError], list[CompileError]]:
        """Parse compiler output for errors and warnings."""
        errors = []
        warnings = []
        
        for match in self.ERROR_PATTERN.finditer(output):
            filename, line, column, level, error_code, message = match.groups()
            
            error = CompileError(
                line=int(line),
                column=int(column),
                error_type=self._classify_error(message),
                message=message.strip(),
                code=error_code
            )
            
            # Check if auto-fixable
            error.auto_fixable = self._is_auto_fixable(error)
            if error.auto_fixable:
                error.fix_suggestion = self._get_fix_suggestion(error)
            
            if level == "error":
                errors.append(error)
            else:
                warnings.append(error)
        
        return errors, warnings
    
    def _classify_error(self, message: str) -> CompileErrorType:
        """Classify the type of compilation error."""
        if self.MISSING_INCLUDE_PATTERN.search(message):
            return CompileErrorType.MISSING_INCLUDE
        elif self.UNDEFINED_VAR_PATTERN.search(message):
            return CompileErrorType.UNDEFINED_VARIABLE
        elif self.UNDEFINED_FUNC_PATTERN.search(message):
            return CompileErrorType.UNDEFINED_FUNCTION
        elif self.MISSING_SEMICOLON_PATTERN.search(message):
            return CompileErrorType.MISSING_SEMICOLON
        elif "type mismatch" in message.lower():
            return CompileErrorType.TYPE_MISMATCH
        elif any(x in message.lower() for x in ["syntax", "unexpected", "expected"]):
            return CompileErrorType.SYNTAX
        else:
            return CompileErrorType.UNKNOWN
    
    def _is_auto_fixable(self, error: CompileError) -> bool:
        """Check if an error can be automatically fixed."""
        return error.error_type in [
            CompileErrorType.MISSING_INCLUDE,
            CompileErrorType.MISSING_SEMICOLON,
        ]
    
    def _get_fix_suggestion(self, error: CompileError) -> Optional[str]:
        """Get auto-fix suggestion for an error."""
        if error.error_type == CompileErrorType.MISSING_INCLUDE:
            match = self.MISSING_INCLUDE_PATTERN.search(error.message)
            if match:
                include_file = match.group(1)
                if include_file in self.STANDARD_INCLUDES:
                    return f"Add: {self.STANDARD_INCLUDES[include_file]}"
        
        elif error.error_type == CompileErrorType.MISSING_SEMICOLON:
            return f"Add semicolon at line {error.line}"
        
        return None
    
    def _try_auto_fix(self, code: str, errors: list[CompileError]) -> Optional[str]:
        """
        Attempt to automatically fix compilation errors.
        
        Returns fixed code or None if no fixes applied.
        """
        fixed_code = code
        fixes_applied = False
        
        # Collect missing includes
        missing_includes = set()
        for error in errors:
            if error.error_type == CompileErrorType.MISSING_INCLUDE:
                match = self.MISSING_INCLUDE_PATTERN.search(error.message)
                if match:
                    include_file = match.group(1)
                    if include_file in self.STANDARD_INCLUDES:
                        missing_includes.add(self.STANDARD_INCLUDES[include_file])
        
        # Add missing includes at the top (after #property lines)
        if missing_includes:
            lines = fixed_code.split("\n")
            insert_idx = 0
            
            # Find the last #property line
            for i, line in enumerate(lines):
                if line.strip().startswith("#property"):
                    insert_idx = i + 1
            
            # Insert includes
            for include in sorted(missing_includes):
                if include not in fixed_code:
                    lines.insert(insert_idx, include)
                    insert_idx += 1
                    fixes_applied = True
            
            fixed_code = "\n".join(lines)
        
        # Fix missing semicolons
        lines = fixed_code.split("\n")
        for error in errors:
            if error.error_type == CompileErrorType.MISSING_SEMICOLON:
                line_idx = error.line - 1
                if 0 <= line_idx < len(lines):
                    line = lines[line_idx].rstrip()
                    if not line.endswith(";") and not line.endswith("{") and not line.endswith("}"):
                        lines[line_idx] = line + ";"
                        fixes_applied = True
        
        fixed_code = "\n".join(lines)
        
        return fixed_code if fixes_applied else None
    
    def get_error_summary(self, result: CompilationResult) -> str:
        """Generate a human-readable error summary."""
        if result.success:
            return f"✅ Compilation successful ({result.compile_attempts} attempt(s))"
        
        summary = f"❌ Compilation failed with {result.error_count} error(s)"
        
        if result.warning_count > 0:
            summary += f" and {result.warning_count} warning(s)"
        
        summary += f" after {result.compile_attempts} attempt(s)"
        
        # Add error details
        for error in result.errors[:5]:  # Show first 5 errors
            summary += f"\n  Line {error.line}: {error.message}"
            if error.fix_suggestion:
                summary += f" (Fix: {error.fix_suggestion})"
        
        if len(result.errors) > 5:
            summary += f"\n  ... and {len(result.errors) - 5} more errors"
        
        return summary
