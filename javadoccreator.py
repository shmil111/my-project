"""
Java Documentation Creator - Generates Java SE compliant documentation.
Based on Java SE specifications from java.sun.com
"""
import javalang
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from jinja2 import Environment, FileSystemLoader
import logging
from datetime import datetime
import re

@dataclass
class JavaEntity:
    """Represents a Java code entity."""
    name: str
    type: str  # class, interface, enum, method
    package: str
    modifiers: List[str]
    annotations: List[str]
    javadoc: str
    params: List[Dict[str, str]]
    returns: Optional[str]
    throws: List[Dict[str, str]]
    examples: List[str]
    since_version: str
    deprecated: bool
    see_also: List[str]

class JavaDocCreator:
    def __init__(self, project_root: str = "."):
        """Initialize Java documentation creator."""
        self.project_root = Path(project_root)
        self.templates_dir = self.project_root / "templates/java"
        self.docs_dir = self.project_root / "javadoc"
        
        # Setup directories and templates
        self._setup_templates()
        self.env = Environment(loader=FileSystemLoader(str(self.templates_dir)))
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _setup_templates(self):
        """Create Java-specific documentation templates."""
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.docs_dir.mkdir(exist_ok=True)
        
        templates = {
            "package.html": """<!DOCTYPE HTML>
<html lang="en">
<head>
    <title>{{ package.name }}</title>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <link rel="stylesheet" type="text/css" href="../stylesheet.css">
</head>
<body>
<main role="main">
<div class="header">
<h1 title="Package" class="title">Package {{ package.name }}</h1>
</div>

<div class="description">
{{ package.description }}
</div>

<div class="summary">
<ul class="summary-list">
{% for class in package.classes %}
    <li>
        <a href="{{ class.name }}.html">{{ class.name }}</a>
        <div class="type-signature">{{ class.modifiers|join(' ') }} class</div>
        <div class="description">{{ class.javadoc.split('\n')[0] }}</div>
    </li>
{% endfor %}
</ul>
</div>
</main>
</body>
</html>""",
            "class.html": """<!DOCTYPE HTML>
<html lang="en">
<head>
    <title>{{ class.name }}</title>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <link rel="stylesheet" type="text/css" href="../stylesheet.css">
</head>
<body>
<main role="main">
<div class="header">
<h1 title="Class" class="title">{{ class.type }} {{ class.name }}</h1>
</div>

<div class="description">
{{ class.javadoc }}

{% if class.since_version %}
<div class="block">Since: {{ class.since_version }}</div>
{% endif %}

{% if class.deprecated %}
<div class="deprecation-block">
<span class="deprecated-label">Deprecated.</span>
</div>
{% endif %}
</div>

<div class="summary">
<h2>Method Summary</h2>
{% for method in class.methods %}
    <div class="member-signature">
        {{ method.modifiers|join(' ') }} 
        {{ method.returns if method.returns else 'void' }}
        <span class="member-name">{{ method.name }}</span>
        ({% for param in method.params %}{{ param.type }} {{ param.name }}{% if not loop.last %}, {% endif %}{% endfor %})
    </div>
    <div class="description">{{ method.javadoc.split('\n')[0] }}</div>
{% endfor %}
</div>

<div class="details">
<h2>Method Details</h2>
{% for method in class.methods %}
    <div class="method-details">
        <h3>{{ method.name }}</h3>
        <div class="member-signature">
            {{ method.modifiers|join(' ') }} 
            {{ method.returns if method.returns else 'void' }}
            <span class="member-name">{{ method.name }}</span>
            ({% for param in method.params %}{{ param.type }} {{ param.name }}{% if not loop.last %}, {% endif %}{% endfor %})
        </div>
        
        <div class="description">{{ method.javadoc }}</div>
        
        {% if method.params %}
        <div class="parameters">
            <h4>Parameters:</h4>
            <ul>
            {% for param in method.params %}
                <li><code>{{ param.name }}</code> - {{ param.description }}</li>
            {% endfor %}
            </ul>
        </div>
        {% endif %}
        
        {% if method.returns %}
        <div class="returns">
            <h4>Returns:</h4>
            <div class="block">{{ method.returns_description }}</div>
        </div>
        {% endif %}
        
        {% if method.throws %}
        <div class="throws">
            <h4>Throws:</h4>
            <ul>
            {% for exception in method.throws %}
                <li><code>{{ exception.type }}</code> - {{ exception.description }}</li>
            {% endfor %}
            </ul>
        </div>
        {% endif %}
        
        {% if method.examples %}
        <div class="examples">
            <h4>Example:</h4>
            <pre>{{ method.examples[0] }}</pre>
        </div>
        {% endif %}
    </div>
{% endfor %}
</div>
</main>
</body>
</html>""",
            "stylesheet.css": """
body {
    font-family: 'DejaVu Sans', Arial, Helvetica, sans-serif;
    font-size: 14px;
    line-height: 1.5;
    color: #333;
    background-color: #fff;
    margin: 0;
    padding: 20px;
}

.header {
    margin-bottom: 20px;
}

.title {
    font-size: 24px;
    font-weight: bold;
    color: #1565C0;
}

.description {
    margin: 15px 0;
}

.summary {
    margin: 20px 0;
}

.summary-list {
    list-style: none;
    padding: 0;
}

.summary-list li {
    margin: 10px 0;
    padding: 10px;
    border-left: 4px solid #1565C0;
    background-color: #f8f9fa;
}

.type-signature {
    color: #666;
    font-size: 12px;
}

.member-signature {
    font-family: monospace;
    background-color: #f8f9fa;
    padding: 10px;
    margin: 5px 0;
}

.member-name {
    font-weight: bold;
    color: #1565C0;
}

.method-details {
    margin: 20px 0;
    padding: 20px;
    border: 1px solid #ddd;
    border-radius: 4px;
}

.parameters, .returns, .throws, .examples {
    margin: 15px 0;
}

.block {
    margin: 10px 0;
}

.deprecated-label {
    color: #dc3545;
    font-weight: bold;
}

pre {
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: 4px;
    overflow-x: auto;
}

code {
    font-family: monospace;
    background-color: #f1f3f4;
    padding: 2px 4px;
    border-radius: 3px;
}
"""
        }
        
        for name, content in templates.items():
            template_path = self.templates_dir / name
            if not template_path.exists():
                template_path.write_text(content)
    
    def analyze_java(self, filepath: str) -> List[JavaEntity]:
        """Analyze Java source file."""
        entities = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        try:
            tree = javalang.parse.parse(content)
            
            # Get package info
            package = next(tree.filter(javalang.tree.PackageDeclaration), None)
            package_name = package.name if package else "default"
            
            # Process classes
            for cls in tree.filter(javalang.tree.ClassDeclaration):
                entities.append(self._analyze_class(cls, package_name))
                
            # Process interfaces
            for interface in tree.filter(javalang.tree.InterfaceDeclaration):
                entities.append(self._analyze_interface(interface, package_name))
                
        except Exception as e:
            self.logger.error(f"Error parsing {filepath}: {str(e)}")
            
        return entities
    
    def _analyze_class(self, node, package_name: str) -> JavaEntity:
        """Analyze a Java class."""
        javadoc = self._extract_javadoc(node.documentation)
        
        return JavaEntity(
            name=node.name,
            type="class",
            package=package_name,
            modifiers=node.modifiers,
            annotations=[str(a) for a in node.annotations],
            javadoc=javadoc["description"],
            params=[],
            returns=None,
            throws=[],
            examples=javadoc.get("examples", []),
            since_version=javadoc.get("since", ""),
            deprecated="@deprecated" in str(node.annotations),
            see_also=javadoc.get("see", [])
        )
    
    def _analyze_interface(self, node, package_name: str) -> JavaEntity:
        """Analyze a Java interface."""
        javadoc = self._extract_javadoc(node.documentation)
        
        return JavaEntity(
            name=node.name,
            type="interface",
            package=package_name,
            modifiers=node.modifiers,
            annotations=[str(a) for a in node.annotations],
            javadoc=javadoc["description"],
            params=[],
            returns=None,
            throws=[],
            examples=javadoc.get("examples", []),
            since_version=javadoc.get("since", ""),
            deprecated="@deprecated" in str(node.annotations),
            see_also=javadoc.get("see", [])
        )
    
    def _extract_javadoc(self, docstring: str) -> Dict[str, Any]:
        """Extract information from Javadoc comment."""
        if not docstring:
            return {"description": ""}
            
        result = {
            "description": "",
            "params": [],
            "returns": None,
            "throws": [],
            "examples": [],
            "since": "",
            "see": []
        }
        
        lines = docstring.split('\n')
        current_section = "description"
        current_text = []
        
        for line in lines:
            line = line.strip().strip('*')
            
            if line.startswith('@param'):
                if current_text:
                    result[current_section] = ' '.join(current_text).strip()
                current_section = "params"
                param_match = re.match(r'@param\s+(\w+)\s+(.*)', line)
                if param_match:
                    result["params"].append({
                        "name": param_match.group(1),
                        "description": param_match.group(2)
                    })
                current_text = []
            elif line.startswith('@return'):
                if current_text:
                    result[current_section] = ' '.join(current_text).strip()
                current_section = "returns"
                current_text = [line[7:].strip()]
            elif line.startswith('@throws'):
                if current_text:
                    result[current_section] = ' '.join(current_text).strip()
                current_section = "throws"
                throws_match = re.match(r'@throws\s+(\w+)\s+(.*)', line)
                if throws_match:
                    result["throws"].append({
                        "type": throws_match.group(1),
                        "description": throws_match.group(2)
                    })
                current_text = []
            elif line.startswith('@since'):
                result["since"] = line[6:].strip()
            elif line.startswith('@see'):
                result["see"].append(line[4:].strip())
            elif line.startswith('@example'):
                current_section = "examples"
                current_text = []
            else:
                current_text.append(line)
        
        if current_text:
            result[current_section] = ' '.join(current_text).strip()
            
        return result
    
    def create_documentation(self, source_dir: str, output_dir: str = None):
        """Create Java documentation."""
        source_path = Path(source_dir)
        output_path = Path(output_dir) if output_dir else self.docs_dir
        output_path.mkdir(exist_ok=True)
        
        # Copy stylesheet
        stylesheet = self.templates_dir / "stylesheet.css"
        if stylesheet.exists():
            output_stylesheet = output_path / "stylesheet.css"
            output_stylesheet.write_text(stylesheet.read_text())
        
        # Track packages and their contents
        packages: Dict[str, List[JavaEntity]] = {}
        
        # Process Java files
        for filepath in source_path.rglob("*.java"):
            try:
                entities = self.analyze_java(str(filepath))
                for entity in entities:
                    if entity.package not in packages:
                        packages[entity.package] = []
                    packages[entity.package].append(entity)
                    
                    # Generate entity documentation
                    self._generate_entity_doc(entity, output_path)
                    
            except Exception as e:
                self.logger.error(f"Error processing {filepath}: {str(e)}")
        
        # Generate package documentation
        for package_name, entities in packages.items():
            self._generate_package_doc(package_name, entities, output_path)
        
        # Generate index
        self._create_index(output_path, packages)
    
    def _generate_entity_doc(self, entity: JavaEntity, output_path: Path):
        """Generate documentation for a Java entity."""
        template = self.env.get_template(f"{entity.type}.html")
        
        # Create package directory
        package_dir = output_path / entity.package.replace('.', '/')
        package_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate documentation
        doc_path = package_dir / f"{entity.name}.html"
        content = template.render(**{entity.type: entity})
        doc_path.write_text(content)
        
        self.logger.info(f"Created documentation: {doc_path}")
    
    def _generate_package_doc(self, package_name: str, entities: List[JavaEntity], output_path: Path):
        """Generate package documentation."""
        template = self.env.get_template("package.html")
        
        # Create package directory
        package_dir = output_path / package_name.replace('.', '/')
        package_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate documentation
        doc_path = package_dir / "package.html"
        content = template.render(
            package={
                "name": package_name,
                "description": "Package documentation",
                "classes": [e for e in entities if e.type == "class"],
                "interfaces": [e for e in entities if e.type == "interface"]
            }
        )
        doc_path.write_text(content)
        
        self.logger.info(f"Created package documentation: {doc_path}")
    
    def _create_index(self, output_path: Path, packages: Dict[str, List[JavaEntity]]):
        """Create documentation index."""
        index_content = [
            "<!DOCTYPE HTML>",
            "<html lang=\"en\">",
            "<head>",
            "    <title>API Documentation</title>",
            "    <link rel=\"stylesheet\" type=\"text/css\" href=\"stylesheet.css\">",
            "</head>",
            "<body>",
            "<main role=\"main\">",
            "<h1>API Documentation</h1>",
            "",
            f"<p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>",
            "",
            "<h2>Packages</h2>",
            "<ul>"
        ]
        
        for package_name, entities in sorted(packages.items()):
            index_content.extend([
                f"<li><a href=\"{package_name.replace('.', '/')}/package.html\">{package_name}</a>",
                "    <ul>"
            ])
            
            for entity in sorted(entities, key=lambda e: e.name):
                index_content.append(
                    f"        <li><a href=\"{package_name.replace('.', '/')}/{entity.name}.html\">"
                    f"{entity.type} {entity.name}</a></li>"
                )
            
            index_content.append("    </ul>")
            index_content.append("</li>")
        
        index_content.extend([
            "</ul>",
            "</main>",
            "</body>",
            "</html>"
        ])
        
        index_path = output_path / "index.html"
        index_path.write_text('\n'.join(index_content))
        self.logger.info(f"Created index: {index_path}")

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Java documentation generator")
    parser.add_argument('source', help="Source code directory")
    parser.add_argument('--output', '-o', help="Output directory")
    parser.add_argument('--templates', '-t', help="Templates directory")
    args = parser.parse_args()
    
    creator = JavaDocCreator()
    if args.templates:
        creator.templates_dir = Path(args.templates)
    
    creator.create_documentation(args.source, args.output)

if __name__ == "__main__":
    main() 