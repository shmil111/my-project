"""
Documentation Generator - Creates and manages documentation templates and content.
"""
import os
import yaml
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from typing import Dict, List, Optional
import shutil

class DocGenerator:
    def __init__(self, template_dir: str = "templates"):
        """Initialize the document generator."""
        self.template_dir = template_dir
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self._ensure_template_dir()
        
    def _ensure_template_dir(self):
        """Ensure template directory exists with base templates."""
        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir)
            self._create_base_templates()
    
    def _create_base_templates(self):
        """Create base document templates."""
        templates = {
            "api.md": """# {{title}}

## Overview
{{description}}

## API Endpoints

{% for endpoint in endpoints %}
### {{endpoint.name}}
- Method: {{endpoint.method}}
- Path: {{endpoint.path}}
- Description: {{endpoint.description}}

#### Parameters
{% for param in endpoint.parameters %}
- {{param.name}} ({{param.type}}): {{param.description}}
{% endfor %}

#### Response
```json
{{endpoint.response_example}}
```
{% endfor %}
""",
            "guide.md": """# {{title}}

## Introduction
{{introduction}}

## Prerequisites
{% for req in prerequisites %}
- {{req}}
{% endfor %}

## Steps
{% for step in steps %}
### {{loop.index}}. {{step.title}}
{{step.description}}

{% if step.code %}
```{{step.language}}
{{step.code}}
```
{% endif %}
{% endfor %}

## Troubleshooting
{% for issue in troubleshooting %}
### {{issue.problem}}
{{issue.solution}}
{% endfor %}
""",
            "component.md": """# {{name}} Component

## Purpose
{{purpose}}

## Interface
```typescript
{{interface}}
```

## Usage
{{usage}}

## Examples
{% for example in examples %}
### {{example.title}}
```{{example.language}}
{{example.code}}
```
{% endfor %}
""",
            "readme.md": """# {{project_name}}

{{description}}

## Features
{% for feature in features %}
- {{feature}}
{% endfor %}

## Installation
```bash
{{installation}}
```

## Quick Start
{{quick_start}}

## Documentation
{{documentation}}

## Contributing
{{contributing}}

## License
{{license}}
"""
        }
        
        for name, content in templates.items():
            path = os.path.join(self.template_dir, name)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
    
    def generate_doc(self, template: str, output_path: str, context: Dict) -> str:
        """Generate a document from a template."""
        template = self.env.get_template(template)
        content = template.render(**context)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return output_path
    
    def generate_api_doc(self, api_data: Dict, output_path: str) -> str:
        """Generate API documentation."""
        return self.generate_doc("api.md", output_path, api_data)
    
    def generate_guide(self, guide_data: Dict, output_path: str) -> str:
        """Generate a guide document."""
        return self.generate_doc("guide.md", output_path, guide_data)
    
    def generate_component_doc(self, component_data: Dict, output_path: str) -> str:
        """Generate component documentation."""
        return self.generate_doc("component.md", output_path, component_data)
    
    def generate_readme(self, project_data: Dict, output_path: str) -> str:
        """Generate a README file."""
        return self.generate_doc("readme.md", output_path, project_data)
    
    def create_doc_structure(self, project_name: str, base_path: str = ".") -> Dict[str, str]:
        """Create a complete documentation structure."""
        structure = {
            "docs": {
                "api": {},
                "guides": {},
                "components": {},
                "examples": {},
                "assets": {}
            }
        }
        
        # Create directory structure
        root = os.path.join(base_path, project_name)
        for path in self._flatten_structure(structure):
            full_path = os.path.join(root, path)
            os.makedirs(full_path, exist_ok=True)
        
        # Generate initial files
        paths = {
            "readme": self.generate_readme(
                {
                    "project_name": project_name,
                    "description": "Project description",
                    "features": ["Feature 1", "Feature 2"],
                    "installation": "pip install " + project_name,
                    "quick_start": "Quick start guide",
                    "documentation": "See docs/ directory",
                    "contributing": "See CONTRIBUTING.md",
                    "license": "MIT"
                },
                os.path.join(root, "README.md")
            ),
            "api_index": self.generate_api_doc(
                {
                    "title": "API Documentation",
                    "description": "API endpoints overview",
                    "endpoints": []
                },
                os.path.join(root, "docs/api/index.md")
            ),
            "guide_index": self.generate_guide(
                {
                    "title": "User Guide",
                    "introduction": "Getting started",
                    "prerequisites": [],
                    "steps": [],
                    "troubleshooting": []
                },
                os.path.join(root, "docs/guides/index.md")
            )
        }
        
        return paths
    
    def _flatten_structure(self, structure: Dict, parent: str = "") -> List[str]:
        """Flatten directory structure into paths."""
        paths = []
        for key, value in structure.items():
            path = os.path.join(parent, key)
            paths.append(path)
            if isinstance(value, dict):
                paths.extend(self._flatten_structure(value, path))
        return paths
    
    def add_template(self, name: str, content: str):
        """Add a new document template."""
        path = os.path.join(self.template_dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    
    def list_templates(self) -> List[str]:
        """List available templates."""
        return [f for f in os.listdir(self.template_dir) 
                if f.endswith((".md", ".rst", ".txt"))]

def main():
    """Main function for CLI usage."""
    generator = DocGenerator()
    
    # Example: Create new project documentation
    paths = generator.create_doc_structure("example_project")
    print("Created documentation structure:")
    for name, path in paths.items():
        print(f"- {name}: {path}")
    
    # Example: Generate API documentation
    api_doc = generator.generate_api_doc(
        {
            "title": "Example API",
            "description": "API documentation example",
            "endpoints": [
                {
                    "name": "Get User",
                    "method": "GET",
                    "path": "/users/{id}",
                    "description": "Retrieve user details",
                    "parameters": [
                        {
                            "name": "id",
                            "type": "integer",
                            "description": "User ID"
                        }
                    ],
                    "response_example": '{"id": 1, "name": "Example User"}'
                }
            ]
        },
        "example_project/docs/api/users.md"
    )
    print(f"\nGenerated API documentation: {api_doc}")

if __name__ == "__main__":
    main() 