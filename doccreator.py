"""
Documentation Creator - Automatically generates and structures documentation.
"""
import os
import ast
import inspect
from typing import Dict, List, Optional, Any
from pathlib import Path
import re
from jinja2 import Environment, FileSystemLoader
import yaml
from docrephraser import DocRephraser
import importlib
import logging
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CodeEntity:
    """Represents a code entity (function, class, module)."""
    name: str
    type: str
    docstring: str
    params: List[Dict[str, str]]
    returns: Optional[str]
    examples: List[str]
    source: str
    dependencies: List[str]

class DocCreator:
    def __init__(self, project_root: str = "."):
        """Initialize documentation creator."""
        self.project_root = Path(project_root)
        self.templates_dir = self.project_root / "templates"
        self.docs_dir = self.project_root / "docs"
        self.rephraser = DocRephraser()
        
        # Setup templates
        self._setup_templates()
        self.env = Environment(loader=FileSystemLoader(str(self.templates_dir)))
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _setup_templates(self):
        """Create template directory and default templates."""
        self.templates_dir.mkdir(exist_ok=True)
        self.docs_dir.mkdir(exist_ok=True)
        
        templates = {
            "module.md": """# {{ module.name }}

{{ module.description }}

## Installation

```bash
pip install {{ module.name }}
```

## Quick Start

```python
{{ module.examples[0] if module.examples else "# Example code here" }}
```

## Features

{% for feature in module.features %}
- {{ feature }}
{% endfor %}

## API Reference

{% for entity in module.entities %}
### {{ entity.name }}

{{ entity.docstring }}

{% if entity.params %}
Parameters:
{% for param in entity.params %}
- `{{ param.name }}` ({{ param.type }}): {{ param.description }}
{% endfor %}
{% endif %}

{% if entity.returns %}
Returns:
{{ entity.returns }}
{% endif %}

{% if entity.examples %}
Example:
```python
{{ entity.examples[0] }}
```
{% endif %}

{% endfor %}
""",
            "class.md": """# {{ class.name }}

{{ class.description }}

## Methods

{% for method in class.methods %}
### {{ method.name }}

{{ method.docstring }}

{% if method.params %}
Parameters:
{% for param in method.params %}
- `{{ param.name }}` ({{ param.type }}): {{ param.description }}
{% endfor %}
{% endif %}

{% if method.returns %}
Returns:
{{ method.returns }}
{% endif %}

{% if method.examples %}
Example:
```python
{{ method.examples[0] }}
```
{% endif %}

{% endfor %}
""",
            "api.md": """# API Reference

{% for section in api_sections %}
## {{ section.name }}

{{ section.description }}

{% for endpoint in section.endpoints %}
### {{ endpoint.method }} {{ endpoint.path }}

{{ endpoint.description }}

{% if endpoint.params %}
Parameters:
{% for param in endpoint.params %}
- `{{ param.name }}` ({{ param.type }}): {{ param.description }}
{% endfor %}
{% endif %}

{% if endpoint.returns %}
Returns:
{{ endpoint.returns }}
{% endif %}

{% if endpoint.example %}
Example:
```python
{{ endpoint.example }}
```
{% endif %}

{% endfor %}
{% endfor %}
"""
        }
        
        for name, content in templates.items():
            template_path = self.templates_dir / name
            if not template_path.exists():
                template_path.write_text(content)
    
    def analyze_code(self, filepath: str) -> List[CodeEntity]:
        """Analyze Python code file and extract documentation info."""
        entities = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
            
        # Get module docstring
        module_doc = ast.get_docstring(tree)
        if module_doc:
            entities.append(CodeEntity(
                name=Path(filepath).stem,
                type="module",
                docstring=module_doc,
                params=[],
                returns=None,
                examples=self._extract_examples(module_doc),
                source="",
                dependencies=self._find_dependencies(tree)
            ))
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                entities.append(self._analyze_function(node))
            elif isinstance(node, ast.ClassDef):
                entities.append(self._analyze_class(node))
        
        return entities
    
    def _analyze_function(self, node: ast.FunctionDef) -> CodeEntity:
        """Analyze a function definition."""
        docstring = ast.get_docstring(node) or ""
        params = []
        
        # Get parameters
        for arg in node.args.args:
            arg_name = arg.arg
            arg_type = ""
            if arg.annotation:
                arg_type = self._get_annotation_name(arg.annotation)
            params.append({
                "name": arg_name,
                "type": arg_type,
                "description": self._extract_param_desc(docstring, arg_name)
            })
        
        return CodeEntity(
            name=node.name,
            type="function",
            docstring=docstring,
            params=params,
            returns=self._extract_returns(docstring),
            examples=self._extract_examples(docstring),
            source=self._get_source(node),
            dependencies=[]
        )
    
    def _analyze_class(self, node: ast.ClassDef) -> CodeEntity:
        """Analyze a class definition."""
        docstring = ast.get_docstring(node) or ""
        methods = []
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(self._analyze_function(item))
        
        return CodeEntity(
            name=node.name,
            type="class",
            docstring=docstring,
            params=[],
            returns=None,
            examples=self._extract_examples(docstring),
            source=self._get_source(node),
            dependencies=[]
        )
    
    def _get_annotation_name(self, node: ast.AST) -> str:
        """Get the string representation of a type annotation."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Subscript):
            return f"{self._get_annotation_name(node.value)}[{self._get_annotation_name(node.slice)}]"
        return ""
    
    def _extract_param_desc(self, docstring: str, param_name: str) -> str:
        """Extract parameter description from docstring."""
        if not docstring:
            return ""
            
        # Look for param in docstring
        pattern = rf":param {param_name}:\s*(.+?)(?:\n\s*:|$)"
        match = re.search(pattern, docstring, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return ""
    
    def _extract_returns(self, docstring: str) -> Optional[str]:
        """Extract return description from docstring."""
        if not docstring:
            return None
            
        pattern = r":returns?:\s*(.+?)(?:\n\s*:|$)"
        match = re.search(pattern, docstring, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_examples(self, docstring: str) -> List[str]:
        """Extract code examples from docstring."""
        if not docstring:
            return []
            
        examples = []
        pattern = r"```python\s*(.*?)\s*```"
        matches = re.finditer(pattern, docstring, re.DOTALL)
        return [m.group(1).strip() for m in matches]
    
    def _get_source(self, node: ast.AST) -> str:
        """Get source code for an AST node."""
        return ast.unparse(node)
    
    def _find_dependencies(self, tree: ast.AST) -> List[str]:
        """Find module dependencies."""
        deps = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                deps.extend(n.name for n in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    deps.append(node.module)
        return sorted(set(deps))
    
    def create_documentation(self, source_dir: str, output_dir: str = None):
        """Create documentation for Python code in directory."""
        source_path = Path(source_dir)
        output_path = Path(output_dir) if output_dir else self.docs_dir
        output_path.mkdir(exist_ok=True)
        
        # Track all entities
        all_entities = []
        
        # Process Python files
        for filepath in source_path.rglob("*.py"):
            try:
                relative_path = filepath.relative_to(source_path)
                doc_path = output_path / relative_path.with_suffix('.md')
                doc_path.parent.mkdir(exist_ok=True)
                
                # Analyze code
                entities = self.analyze_code(str(filepath))
                all_entities.extend(entities)
                
                # Generate documentation
                if entities:
                    content = self._generate_doc(entities[0] if len(entities) == 1 else entities)
                    
                    # Improve content
                    improved_content, _ = self.rephraser.rephrase_document(content)
                    
                    # Save documentation
                    doc_path.write_text(improved_content)
                    self.logger.info(f"Created documentation: {doc_path}")
            
            except Exception as e:
                self.logger.error(f"Error processing {filepath}: {str(e)}")
        
        # Generate index
        self._create_index(output_path, all_entities)
    
    def _generate_doc(self, entity_or_entities: Any) -> str:
        """Generate documentation content."""
        if isinstance(entity_or_entities, list):
            # Multiple entities - use module template
            template = self.env.get_template("module.md")
            return template.render(
                module={
                    "name": entity_or_entities[0].name,
                    "description": entity_or_entities[0].docstring,
                    "examples": entity_or_entities[0].examples,
                    "features": [],
                    "entities": entity_or_entities[1:]
                }
            )
        else:
            # Single entity - use appropriate template
            template_name = f"{entity_or_entities.type}.md"
            template = self.env.get_template(template_name)
            return template.render(**{entity_or_entities.type: entity_or_entities})
    
    def _create_index(self, output_path: Path, entities: List[CodeEntity]):
        """Create documentation index."""
        modules = [e for e in entities if e.type == "module"]
        classes = [e for e in entities if e.type == "class"]
        functions = [e for e in entities if e.type == "function"]
        
        index_content = [
            "# API Documentation",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Modules",
            ""
        ]
        
        for module in modules:
            index_content.extend([
                f"### {module.name}",
                "",
                module.docstring.split('\n')[0] if module.docstring else "",
                ""
            ])
        
        if classes:
            index_content.extend([
                "## Classes",
                ""
            ])
            for cls in classes:
                index_content.extend([
                    f"### {cls.name}",
                    "",
                    cls.docstring.split('\n')[0] if cls.docstring else "",
                    ""
                ])
        
        if functions:
            index_content.extend([
                "## Functions",
                ""
            ])
            for func in functions:
                index_content.extend([
                    f"### {func.name}",
                    "",
                    func.docstring.split('\n')[0] if func.docstring else "",
                    ""
                ])
        
        index_path = output_path / "index.md"
        index_path.write_text('\n'.join(index_content))
        self.logger.info(f"Created index: {index_path}")

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Documentation creation system")
    parser.add_argument('source', help="Source code directory")
    parser.add_argument('--output', '-o', help="Output directory")
    parser.add_argument('--templates', '-t', help="Templates directory")
    args = parser.parse_args()
    
    creator = DocCreator()
    if args.templates:
        creator.templates_dir = Path(args.templates)
    
    creator.create_documentation(args.source, args.output)

if __name__ == "__main__":
    main() 