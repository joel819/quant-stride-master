"""
MQL5 Parser
Parse MQL5 code structure and identify components.
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MQLFunction:
    """Represents an MQL5 function."""
    name: str
    return_type: str
    parameters: list[str]
    start_line: int
    end_line: int
    body: str = ""


@dataclass
class MQLVariable:
    """Represents an MQL5 variable."""
    name: str
    var_type: str
    is_input: bool = False
    is_global: bool = False
    default_value: Optional[str] = None
    line: int = 0


@dataclass
class MQLInclude:
    """Represents an MQL5 include directive."""
    path: str
    line: int


@dataclass
class MQLStructure:
    """Complete parsed MQL5 code structure."""
    functions: list[MQLFunction] = field(default_factory=list)
    variables: list[MQLVariable] = field(default_factory=list)
    includes: list[MQLInclude] = field(default_factory=list)
    properties: dict[str, str] = field(default_factory=dict)
    enums: list[str] = field(default_factory=list)
    
    def has_function(self, name: str) -> bool:
        return any(f.name == name for f in self.functions)
    
    def has_variable(self, name: str) -> bool:
        return any(v.name == name for v in self.variables)
    
    def get_function(self, name: str) -> Optional[MQLFunction]:
        for f in self.functions:
            if f.name == name:
                return f
        return None


class MQLParser:
    """
    Parse MQL5 code to extract structure.
    
    Can identify:
    - Functions (OnInit, OnTick, etc.)
    - Input parameters
    - Global variables
    - Include directives
    - Properties
    - Enumerations
    """
    
    # Regex patterns
    INCLUDE_PATTERN = re.compile(r'#include\s*[<"](.+?)[>"]')
    PROPERTY_PATTERN = re.compile(r'#property\s+(\w+)\s+["\']?([^"\'\n]+)["\']?')
    INPUT_PATTERN = re.compile(r'input\s+(\w+[\s\*]*)\s+(\w+)\s*=\s*([^;]+);')
    GLOBAL_PATTERN = re.compile(r'^(int|double|bool|string|datetime|color|ulong|long)\s+(\w+)\s*(?:=\s*([^;]+))?;', re.MULTILINE)
    FUNCTION_PATTERN = re.compile(r'^(\w+[\s\*]*)\s+(\w+)\s*\(([^)]*)\)\s*$', re.MULTILINE)
    ENUM_PATTERN = re.compile(r'enum\s+(\w+)\s*\{([^}]+)\}', re.DOTALL)
    
    def __init__(self):
        self.structure = MQLStructure()
    
    def parse(self, code: str) -> MQLStructure:
        """
        Parse MQL5 code and extract structure.
        
        Args:
            code: MQL5 source code
            
        Returns:
            MQLStructure with all components
        """
        self.structure = MQLStructure()
        
        self._parse_includes(code)
        self._parse_properties(code)
        self._parse_inputs(code)
        self._parse_globals(code)
        self._parse_enums(code)
        self._parse_functions(code)
        
        return self.structure
    
    def _parse_includes(self, code: str):
        """Extract include directives."""
        for i, line in enumerate(code.split('\n'), 1):
            match = self.INCLUDE_PATTERN.search(line)
            if match:
                self.structure.includes.append(MQLInclude(
                    path=match.group(1),
                    line=i
                ))
    
    def _parse_properties(self, code: str):
        """Extract property declarations."""
        for match in self.PROPERTY_PATTERN.finditer(code):
            prop_name = match.group(1)
            prop_value = match.group(2).strip()
            self.structure.properties[prop_name] = prop_value
    
    def _parse_inputs(self, code: str):
        """Extract input parameters."""
        for i, line in enumerate(code.split('\n'), 1):
            match = self.INPUT_PATTERN.search(line)
            if match:
                self.structure.variables.append(MQLVariable(
                    name=match.group(2),
                    var_type=match.group(1).strip(),
                    is_input=True,
                    default_value=match.group(3).strip(),
                    line=i
                ))
    
    def _parse_globals(self, code: str):
        """Extract global variables."""
        # Find code outside of functions
        lines = code.split('\n')
        in_function = False
        brace_count = 0
        
        for i, line in enumerate(lines, 1):
            # Track brace depth
            brace_count += line.count('{') - line.count('}')
            
            if brace_count > 0:
                in_function = True
            else:
                in_function = False
            
            if not in_function:
                match = self.GLOBAL_PATTERN.search(line)
                if match:
                    self.structure.variables.append(MQLVariable(
                        name=match.group(2),
                        var_type=match.group(1),
                        is_global=True,
                        default_value=match.group(3).strip() if match.group(3) else None,
                        line=i
                    ))
    
    def _parse_enums(self, code: str):
        """Extract enum definitions."""
        for match in self.ENUM_PATTERN.finditer(code):
            self.structure.enums.append(match.group(1))
    
    def _parse_functions(self, code: str):
        """Extract function definitions."""
        lines = code.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for function signature
            if '(' in line and ')' in line and '{' not in line:
                # Check next line for opening brace
                if i + 1 < len(lines) and '{' in lines[i + 1]:
                    match = self.FUNCTION_PATTERN.match(line)
                    if match:
                        func = self._extract_function(lines, i, match)
                        if func:
                            self.structure.functions.append(func)
                            i = func.end_line
                            continue
            
            # Single line function start
            if '(' in line and ')' in line and '{' in line:
                # Extract function signature
                sig_end = line.find('{')
                sig = line[:sig_end].strip()
                match = self.FUNCTION_PATTERN.match(sig)
                if match:
                    func = self._extract_function(lines, i, match)
                    if func:
                        self.structure.functions.append(func)
                        i = func.end_line
                        continue
            
            i += 1
    
    def _extract_function(
        self,
        lines: list[str],
        start_line: int,
        match
    ) -> Optional[MQLFunction]:
        """Extract a complete function including body."""
        return_type = match.group(1).strip()
        name = match.group(2)
        params = match.group(3).strip()
        
        # Find function body
        brace_count = 0
        body_lines = []
        end_line = start_line
        
        for i in range(start_line, len(lines)):
            line = lines[i]
            
            brace_count += line.count('{')
            brace_count -= line.count('}')
            
            if brace_count > 0 or (i == start_line and '{' not in line):
                body_lines.append(line)
            elif brace_count == 0 and '{' in ''.join(body_lines):
                body_lines.append(line)
                end_line = i
                break
        
        return MQLFunction(
            name=name,
            return_type=return_type,
            parameters=[p.strip() for p in params.split(',') if p.strip()],
            start_line=start_line + 1,  # 1-indexed
            end_line=end_line + 1,
            body='\n'.join(body_lines)
        )
    
    def validate_structure(self, structure: MQLStructure) -> list[str]:
        """
        Validate that required components exist.
        
        Returns list of issues.
        """
        issues = []
        
        # Required functions
        required_funcs = ["OnInit", "OnTick", "OnDeinit"]
        for func in required_funcs:
            if not structure.has_function(func):
                issues.append(f"Missing required function: {func}")
        
        # Required properties
        if "copyright" not in structure.properties:
            issues.append("Missing #property copyright")
        if "version" not in structure.properties:
            issues.append("Missing #property version")
        
        return issues
    
    def get_missing_components(
        self,
        structure: MQLStructure,
        required: list[str]
    ) -> list[str]:
        """Get list of missing required components."""
        missing = []
        
        for item in required:
            if not structure.has_function(item) and not structure.has_variable(item):
                missing.append(item)
        
        return missing
