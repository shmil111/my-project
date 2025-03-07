#!/usr/bin/env python3
"""
Documentation Manager - Manages markdown documentation files and their relationships.
"""

import os
import sys
import psycopg2
from datetime import datetime
import markdown
import re
from typing import List, Dict, Optional

class DocManager:
    def __init__(self, db_name: str = "eveplugins"):
        """Initialize documentation manager."""
        self.conn = psycopg2.connect(f"dbname={db_name}")
        self.cur = self.conn.cursor()
        
    def scan_docs(self, directory: str = ".") -> List[Dict]:
        """Scan directory for markdown files and update database."""
        docs = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.md'):
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Extract title from first line
                    title = content.split('\n')[0].strip('# ')
                    
                    # Count words
                    word_count = len(re.findall(r'\w+', content))
                    
                    # Check for TODOs
                    has_todo = bool(re.search(r'\btodo\b', content.lower()))
                    
                    # Update database
                    self.cur.execute("""
                        INSERT INTO documentation_files 
                        (filename, title, word_count, has_todo)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (filename) DO UPDATE
                        SET title = EXCLUDED.title,
                            word_count = EXCLUDED.word_count,
                            has_todo = EXCLUDED.has_todo,
                            last_modified = CURRENT_TIMESTAMP
                    """, (file, title, word_count, has_todo))
                    
                    docs.append({
                        'filename': file,
                        'title': title,
                        'word_count': word_count,
                        'has_todo': has_todo
                    })
                    
        self.conn.commit()
        return docs
    
    def find_links(self) -> List[Dict]:
        """Find links between documentation files."""
        self.cur.execute("SELECT filename, title FROM documentation_files")
        docs = {row[0]: row[1] for row in self.cur.fetchall()}
        
        links = []
        for filename in docs:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Find markdown links
            for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', content):
                target = match.group(2)
                if target in docs:
                    self.cur.execute("""
                        INSERT INTO doc_links (source_doc_id, target_doc_id, link_type)
                        SELECT s.id, t.id, 'reference'
                        FROM documentation_files s, documentation_files t
                        WHERE s.filename = %s AND t.filename = %s
                        ON CONFLICT DO NOTHING
                    """, (filename, target))
                    
                    links.append({
                        'source': filename,
                        'target': target,
                        'type': 'reference'
                    })
                    
        self.conn.commit()
        return links
    
    def extract_todos(self) -> List[Dict]:
        """Extract TODOs from documentation files."""
        todos = []
        self.cur.execute("SELECT id, filename FROM documentation_files WHERE has_todo = true")
        
        for doc_id, filename in self.cur.fetchall():
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Find TODO items
            for match in re.finditer(r'(?:TODO|FIXME):\s*(.+)(?:\n|$)', content, re.IGNORECASE):
                task = match.group(1).strip()
                
                self.cur.execute("""
                    INSERT INTO doc_todos (doc_id, task_description)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    RETURNING id
                """, (doc_id, task))
                
                if self.cur.fetchone():  # Only append if inserted
                    todos.append({
                        'filename': filename,
                        'task': task
                    })
                    
        self.conn.commit()
        return todos
    
    def generate_report(self) -> Dict:
        """Generate documentation status report."""
        report = {
            'total_docs': 0,
            'total_todos': 0,
            'categories': {},
            'needs_update': [],
            'orphaned': []
        }
        
        # Get document counts
        self.cur.execute("""
            SELECT 
                COUNT(*) as total_docs,
                COUNT(CASE WHEN has_todo THEN 1 END) as docs_with_todos,
                COUNT(CASE WHEN status = 'NeedsUpdate' THEN 1 END) as needs_update
            FROM documentation_files
        """)
        counts = self.cur.fetchone()
        report['total_docs'] = counts[0]
        report['docs_with_todos'] = counts[1]
        report['needs_update_count'] = counts[2]
        
        # Get category breakdown
        self.cur.execute("""
            SELECT 
                category,
                COUNT(*) as doc_count
            FROM documentation_files
            WHERE category IS NOT NULL
            GROUP BY category
        """)
        report['categories'] = {row[0]: row[1] for row in self.cur.fetchall()}
        
        # Get documents needing update
        self.cur.execute("""
            SELECT filename, title
            FROM documentation_files
            WHERE status = 'NeedsUpdate'
        """)
        report['needs_update'] = [{'filename': row[0], 'title': row[1]} 
                                for row in self.cur.fetchall()]
        
        # Get orphaned documents (no incoming links)
        self.cur.execute("""
            SELECT df.filename, df.title
            FROM documentation_files df
            LEFT JOIN doc_links dl ON df.id = dl.target_doc_id
            WHERE dl.id IS NULL
            AND df.filename != 'README.md'
        """)
        report['orphaned'] = [{'filename': row[0], 'title': row[1]} 
                            for row in self.cur.fetchall()]
        
        return report
    
    def close(self):
        """Close database connection."""
        self.cur.close()
        self.conn.close()

def main():
    """Main function."""
    doc_manager = DocManager()
    
    try:
        print("Scanning documentation files...")
        docs = doc_manager.scan_docs()
        print(f"Found {len(docs)} markdown files")
        
        print("\nFinding document links...")
        links = doc_manager.find_links()
        print(f"Found {len(links)} links between documents")
        
        print("\nExtracting TODOs...")
        todos = doc_manager.extract_todos()
        print(f"Found {len(todos)} TODO items")
        
        print("\nGenerating report...")
        report = doc_manager.generate_report()
        
        print("\nDocumentation Status Report")
        print("=" * 30)
        print(f"Total Documents: {report['total_docs']}")
        print(f"Documents with TODOs: {report['docs_with_todos']}")
        print(f"Documents Needing Update: {report['needs_update_count']}")
        
        print("\nCategory Breakdown:")
        for category, count in report['categories'].items():
            print(f"  {category}: {count} documents")
        
        if report['needs_update']:
            print("\nDocuments Needing Update:")
            for doc in report['needs_update']:
                print(f"  {doc['filename']}: {doc['title']}")
        
        if report['orphaned']:
            print("\nOrphaned Documents:")
            for doc in report['orphaned']:
                print(f"  {doc['filename']}: {doc['title']}")
                
    finally:
        doc_manager.close()

if __name__ == "__main__":
    main() 