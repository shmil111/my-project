"""
Documentation Automator - Continuously monitors and improves documentation.
"""
import os
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from docrephraser import DocRephraser
from typing import Set, Dict, Optional
import json
from datetime import datetime
import threading
from queue import Queue
import hashlib
from pathlib import Path

class DocAutomator:
    def __init__(self, watch_dir: str = ".", 
                 backup_dir: str = ".docbackups",
                 history_file: str = ".dochistory.json"):
        """Initialize the documentation automator."""
        self.watch_dir = os.path.abspath(watch_dir)
        self.backup_dir = os.path.abspath(backup_dir)
        self.history_file = history_file
        self.rephraser = DocRephraser()
        self.file_queue = Queue()
        self.processed_files: Set[str] = set()
        self.file_hashes: Dict[str, str] = {}
        self.stats: Dict[str, Dict] = {}
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('docautomator.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Ensure directories exist
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Load history
        self._load_history()
        
    def _load_history(self):
        """Load processing history."""
        try:
            with open(self.history_file, 'r') as f:
                history = json.load(f)
                self.file_hashes = history.get('hashes', {})
                self.stats = history.get('stats', {})
        except (FileNotFoundError, json.JSONDecodeError):
            self.file_hashes = {}
            self.stats = {}
    
    def _save_history(self):
        """Save processing history."""
        history = {
            'hashes': self.file_hashes,
            'stats': self.stats,
            'last_update': datetime.now().isoformat()
        }
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def _get_file_hash(self, filepath: str) -> str:
        """Calculate file hash."""
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def _backup_file(self, filepath: str):
        """Create backup of original file."""
        filename = os.path.basename(filepath)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(
            self.backup_dir,
            f"{filename}.{timestamp}.bak"
        )
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        with open(filepath, 'r', encoding='utf-8') as src:
            with open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        return backup_path
    
    def _should_process_file(self, filepath: str) -> bool:
        """Check if file should be processed."""
        if not filepath.endswith(('.md', '.txt')):
            return False
            
        # Check if file has changed
        current_hash = self._get_file_hash(filepath)
        if filepath in self.file_hashes:
            if current_hash == self.file_hashes[filepath]:
                return False
                
        self.file_hashes[filepath] = current_hash
        return True
    
    def _process_file(self, filepath: str):
        """Process a single file."""
        try:
            # Read content
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create backup
            backup_path = self._backup_file(filepath)
            
            # Improve content
            improved_content, metrics = self.rephraser.rephrase_document(content)
            
            # Only save if improvements were made
            if metrics['changes_made'] > 0:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(improved_content)
                
                # Update stats
                self.stats[filepath] = {
                    'last_processed': datetime.now().isoformat(),
                    'changes_made': metrics['changes_made'],
                    'readability_improvement': metrics['readability_improvement'],
                    'backup_path': backup_path
                }
                
                self.logger.info(
                    f"Improved {filepath}: {metrics['changes_made']} changes, "
                    f"{metrics['readability_improvement']:.2f} readability improvement"
                )
            else:
                self.logger.info(f"No improvements needed for {filepath}")
            
            self._save_history()
            
        except Exception as e:
            self.logger.error(f"Error processing {filepath}: {str(e)}")
    
    def process_directory(self, directory: str = None):
        """Process all documentation files in directory."""
        if directory is None:
            directory = self.watch_dir
            
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(('.md', '.txt')):
                    filepath = os.path.join(root, file)
                    if self._should_process_file(filepath):
                        self._process_file(filepath)
    
    def generate_report(self, output_file: str = "docautomator_report.md"):
        """Generate improvement report."""
        report = [
            "# Documentation Improvement Report",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            "",
            f"Total files processed: {len(self.stats)}",
            f"Total improvements made: {sum(s['changes_made'] for s in self.stats.values())}",
            "",
            "## File Details",
            ""
        ]
        
        for filepath, stats in sorted(self.stats.items()):
            report.extend([
                f"### {os.path.basename(filepath)}",
                "",
                f"- Last processed: {stats['last_processed']}",
                f"- Changes made: {stats['changes_made']}",
                f"- Readability improvement: {stats['readability_improvement']:.2f}",
                f"- Backup: {stats['backup_path']}",
                ""
            ])
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
            
        return output_file

class DocEventHandler(FileSystemEventHandler):
    """Handle file system events for documentation files."""
    
    def __init__(self, automator: DocAutomator):
        self.automator = automator
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(('.md', '.txt')):
            self.automator.file_queue.put(event.src_path)

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated documentation improvement system")
    parser.add_argument('--watch', '-w', help="Directory to watch", default=".")
    parser.add_argument('--backup', '-b', help="Backup directory", default=".docbackups")
    parser.add_argument('--report', '-r', help="Generate report", action='store_true')
    args = parser.parse_args()
    
    automator = DocAutomator(args.watch, args.backup)
    
    # Process existing files
    print("Processing existing files...")
    automator.process_directory()
    
    if args.report:
        report_file = automator.generate_report()
        print(f"\nReport generated: {report_file}")
        return
    
    # Start file system observer
    observer = Observer()
    handler = DocEventHandler(automator)
    observer.schedule(handler, args.watch, recursive=True)
    observer.start()
    
    print(f"\nWatching directory: {args.watch}")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            # Process queued files
            while not automator.file_queue.empty():
                filepath = automator.file_queue.get()
                if automator._should_process_file(filepath):
                    automator._process_file(filepath)
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()

if __name__ == "__main__":
    main() 