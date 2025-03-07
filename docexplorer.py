"""
Documentation Explorer - Analyzes and visualizes documentation relationships and insights.
"""
import os
import re
import json
import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import markdown
from bs4 import BeautifulSoup
from docgen import DocGenerator

class DocExplorer:
    def __init__(self, base_path: str = "."):
        """Initialize documentation explorer."""
        self.base_path = base_path
        self.graph = nx.DiGraph()
        self.doc_index = {}
        self.topics = defaultdict(list)
        self.references = defaultdict(set)
        self.complexity_scores = {}
        
    def scan_docs(self) -> Dict[str, Dict]:
        """Scan and analyze documentation files."""
        for root, _, files in os.walk(self.base_path):
            for file in files:
                if file.endswith(('.md', '.rst', '.txt')):
                    path = os.path.join(root, file)
                    rel_path = os.path.relpath(path, self.base_path)
                    
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    doc_info = self._analyze_document(rel_path, content)
                    self.doc_index[rel_path] = doc_info
                    
                    # Add to graph
                    self.graph.add_node(rel_path, **doc_info)
                    
                    # Process references
                    for ref in doc_info['references']:
                        self.graph.add_edge(rel_path, ref)
                        self.references[rel_path].add(ref)
                        
        return self.doc_index
    
    def _analyze_document(self, path: str, content: str) -> Dict:
        """Analyze a single document."""
        # Convert markdown to HTML for better parsing
        html = markdown.markdown(content)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract basic info
        title = soup.find('h1')
        title = title.text if title else path
        
        # Find references
        references = set()
        for link in soup.find_all('a'):
            href = link.get('href', '')
            if href.endswith(('.md', '.rst', '.txt')):
                references.add(href)
                
        # Extract topics
        topics = set()
        for tag in soup.find_all(['h1', 'h2', 'h3']):
            topics.add(tag.text.strip())
            
        # Calculate complexity
        complexity = self._calculate_complexity(content)
        
        return {
            'title': title,
            'path': path,
            'topics': list(topics),
            'references': list(references),
            'complexity': complexity,
            'word_count': len(content.split()),
            'sections': len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
        }
    
    def _calculate_complexity(self, content: str) -> float:
        """Calculate document complexity score."""
        factors = {
            'length': len(content.split()) / 1000,  # Per 1000 words
            'code_blocks': len(re.findall(r'```.*?```', content, re.DOTALL)) * 0.5,
            'sections': len(re.findall(r'^#{1,6}\s', content, re.MULTILINE)) * 0.3,
            'links': len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)) * 0.2,
            'tables': len(re.findall(r'\|.*\|', content)) * 0.4
        }
        return sum(factors.values())
    
    def generate_insights(self) -> Dict:
        """Generate documentation insights."""
        insights = {
            'summary': {
                'total_docs': len(self.doc_index),
                'total_topics': sum(len(doc['topics']) for doc in self.doc_index.values()),
                'total_references': sum(len(doc['references']) for doc in self.doc_index.values()),
                'avg_complexity': sum(doc['complexity'] for doc in self.doc_index.values()) / len(self.doc_index) if self.doc_index else 0
            },
            'topic_clusters': self._find_topic_clusters(),
            'central_docs': self._find_central_documents(),
            'orphaned_docs': self._find_orphaned_documents(),
            'complexity_outliers': self._find_complexity_outliers()
        }
        return insights
    
    def _find_topic_clusters(self) -> List[Dict]:
        """Find clusters of related documents by topic."""
        topic_docs = defaultdict(list)
        for path, doc in self.doc_index.items():
            for topic in doc['topics']:
                topic_docs[topic].append(path)
                
        return [
            {
                'topic': topic,
                'documents': docs,
                'size': len(docs)
            }
            for topic, docs in topic_docs.items()
            if len(docs) > 1  # Only include clusters with multiple docs
        ]
    
    def _find_central_documents(self, top_n: int = 5) -> List[Dict]:
        """Find most central/important documents."""
        if not self.graph:
            return []
            
        # Calculate centrality metrics
        pagerank = nx.pagerank(self.graph)
        betweenness = nx.betweenness_centrality(self.graph)
        
        # Combine metrics
        scores = {
            doc: (pagerank.get(doc, 0) + betweenness.get(doc, 0)) / 2
            for doc in self.doc_index
        }
        
        # Get top documents
        top_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        return [
            {
                'path': doc,
                'score': score,
                'title': self.doc_index[doc]['title'],
                'topics': self.doc_index[doc]['topics']
            }
            for doc, score in top_docs
        ]
    
    def _find_orphaned_documents(self) -> List[Dict]:
        """Find documents with no incoming references."""
        orphaned = []
        for doc in self.doc_index:
            if not any(doc in refs for refs in self.references.values()):
                orphaned.append({
                    'path': doc,
                    'title': self.doc_index[doc]['title'],
                    'topics': self.doc_index[doc]['topics']
                })
        return orphaned
    
    def _find_complexity_outliers(self, threshold: float = 1.5) -> List[Dict]:
        """Find documents with unusually high complexity."""
        complexities = [doc['complexity'] for doc in self.doc_index.values()]
        if not complexities:
            return []
            
        avg_complexity = sum(complexities) / len(complexities)
        outliers = []
        
        for path, doc in self.doc_index.items():
            if doc['complexity'] > avg_complexity * threshold:
                outliers.append({
                    'path': path,
                    'title': doc['title'],
                    'complexity': doc['complexity'],
                    'topics': doc['topics']
                })
                
        return sorted(outliers, key=lambda x: x['complexity'], reverse=True)
    
    def visualize_graph(self, output_path: str = "doc_graph.png"):
        """Generate a visualization of document relationships."""
        plt.figure(figsize=(12, 8))
        
        # Create layout
        pos = nx.spring_layout(self.graph)
        
        # Draw nodes
        nx.draw_networkx_nodes(
            self.graph, pos,
            node_color='lightblue',
            node_size=[
                self.doc_index[node]['complexity'] * 500 
                for node in self.graph.nodes()
            ]
        )
        
        # Draw edges
        nx.draw_networkx_edges(self.graph, pos, edge_color='gray', arrows=True)
        
        # Add labels
        labels = {
            node: self.doc_index[node]['title'][:20] + '...'
            for node in self.graph.nodes()
        }
        nx.draw_networkx_labels(self.graph, pos, labels, font_size=8)
        
        plt.title("Documentation Relationship Graph")
        plt.axis('off')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def generate_report(self, output_path: str = "doc_report.md") -> str:
        """Generate a comprehensive documentation analysis report."""
        insights = self.generate_insights()
        
        # Create report using DocGenerator
        generator = DocGenerator()
        report_data = {
            "title": "Documentation Analysis Report",
            "introduction": f"""
This report provides insights into the documentation structure and relationships.
Total Documents: {insights['summary']['total_docs']}
Total Topics: {insights['summary']['total_topics']}
Average Complexity: {insights['summary']['avg_complexity']:.2f}
            """.strip(),
            "prerequisites": [],
            "steps": [
                {
                    "title": "Central Documents",
                    "description": "These documents are key reference points:\n" +
                        "\n".join(f"- {doc['title']} ({doc['path']})" 
                                for doc in insights['central_docs'])
                },
                {
                    "title": "Topic Clusters",
                    "description": "Related document groups:\n" +
                        "\n".join(f"- {cluster['topic']}: {len(cluster['documents'])} documents"
                                for cluster in insights['topic_clusters'])
                },
                {
                    "title": "Complexity Analysis",
                    "description": "Documents needing review:\n" +
                        "\n".join(f"- {doc['title']} (complexity: {doc['complexity']:.2f})"
                                for doc in insights['complexity_outliers'])
                },
                {
                    "title": "Orphaned Documents",
                    "description": "Documents without references:\n" +
                        "\n".join(f"- {doc['title']} ({doc['path']})"
                                for doc in insights['orphaned_documents'])
                }
            ],
            "troubleshooting": []
        }
        
        return generator.generate_guide(report_data, output_path)

def main():
    """Main function for CLI usage."""
    explorer = DocExplorer()
    
    print("Scanning documentation...")
    explorer.scan_docs()
    
    print("\nGenerating insights...")
    insights = explorer.generate_insights()
    
    print("\nGenerating visualization...")
    graph_path = explorer.visualize_graph()
    
    print("\nGenerating report...")
    report_path = explorer.generate_report()
    
    print(f"\nOutputs:")
    print(f"- Graph: {graph_path}")
    print(f"- Report: {report_path}")
    
    print("\nSummary:")
    print(f"- Total Documents: {insights['summary']['total_docs']}")
    print(f"- Total Topics: {insights['summary']['total_topics']}")
    print(f"- Average Complexity: {insights['summary']['avg_complexity']:.2f}")

if __name__ == "__main__":
    main()