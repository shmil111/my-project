"""
Documentation Management System Web Interface
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from datetime import datetime
from docmanager import DocManager

app = FastAPI(title="Documentation Manager", version="1.0.0")
doc_manager = DocManager()

# Models
class Todo(BaseModel):
    filename: str
    task: str
    priority: Optional[int] = 3
    due_date: Optional[datetime] = None

class Document(BaseModel):
    filename: str
    title: str
    category: Optional[str] = None
    status: str = "Active"

# Routes
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main dashboard."""
    return """
    <html>
        <head>
            <title>Documentation Manager</title>
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        </head>
        <body class="bg-gray-100">
            <div class="container mx-auto px-4 py-8">
                <h1 class="text-4xl font-bold mb-8">Documentation Manager</h1>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <div class="bg-white p-6 rounded-lg shadow-md">
                        <h2 class="text-xl font-semibold mb-4">Quick Actions</h2>
                        <ul class="space-y-2">
                            <li><a href="/docs" class="text-blue-600 hover:underline">API Documentation</a></li>
                            <li><a href="/scan" class="text-blue-600 hover:underline">Scan Documents</a></li>
                            <li><a href="/report" class="text-blue-600 hover:underline">Generate Report</a></li>
                        </ul>
                    </div>
                </div>
            </div>
            <script>
                // Add interactive features here
            </script>
        </body>
    </html>
    """

@app.get("/scan")
async def scan_docs(background_tasks: BackgroundTasks):
    """Trigger document scanning."""
    background_tasks.add_task(doc_manager.scan_docs)
    return {"message": "Document scan initiated"}

@app.get("/report")
async def get_report():
    """Generate documentation report."""
    return doc_manager.generate_report()

@app.get("/docs/{filename}")
async def get_document(filename: str):
    """Get document details."""
    doc = doc_manager.cur.execute(
        "SELECT * FROM documentation_files WHERE filename = %s",
        (filename,)
    )
    if doc:
        return doc
    raise HTTPException(status_code=404, detail="Document not found")

@app.post("/todos")
async def add_todo(todo: Todo):
    """Add a new TODO item."""
    doc_manager.cur.execute(
        "SELECT id FROM documentation_files WHERE filename = %s",
        (todo.filename,)
    )
    doc_id = doc_manager.cur.fetchone()
    if not doc_id:
        raise HTTPException(status_code=404, detail="Document not found")
        
    doc_manager.cur.execute(
        """
        INSERT INTO doc_todos (doc_id, task_description, priority, due_date)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """,
        (doc_id[0], todo.task, todo.priority, todo.due_date)
    )
    doc_manager.conn.commit()
    return {"id": doc_manager.cur.fetchone()[0]}

@app.get("/todos")
async def get_todos(status: Optional[str] = None):
    """Get TODO items."""
    query = "SELECT * FROM pending_todos"
    if status:
        query += f" WHERE status = '{status}'"
    doc_manager.cur.execute(query)
    return doc_manager.cur.fetchall()

@app.put("/docs/{filename}")
async def update_document(filename: str, doc: Document):
    """Update document details."""
    doc_manager.cur.execute(
        """
        UPDATE documentation_files
        SET title = %s, category = %s, status = %s, last_modified = CURRENT_TIMESTAMP
        WHERE filename = %s
        RETURNING id
        """,
        (doc.title, doc.category, doc.status, filename)
    )
    doc_manager.conn.commit()
    if doc_manager.cur.fetchone():
        return {"message": "Document updated"}
    raise HTTPException(status_code=404, detail="Document not found")

@app.get("/categories")
async def get_categories():
    """Get document categories."""
    doc_manager.cur.execute("SELECT * FROM doc_categories")
    return doc_manager.cur.fetchall()

@app.get("/links")
async def get_links(filename: Optional[str] = None):
    """Get document links."""
    query = "SELECT * FROM doc_dependencies"
    if filename:
        query += f" WHERE source_doc = '{filename}' OR target_doc = '{filename}'"
    doc_manager.cur.execute(query)
    return doc_manager.cur.fetchall()

@app.get("/stats")
async def get_stats():
    """Get documentation statistics."""
    doc_manager.cur.execute("""
        SELECT 
            COUNT(*) as total_docs,
            COUNT(CASE WHEN has_todo THEN 1 END) as docs_with_todos,
            COUNT(CASE WHEN status = 'NeedsUpdate' THEN 1 END) as needs_update,
            AVG(word_count) as avg_word_count
        FROM documentation_files
    """)
    return doc_manager.cur.fetchone()

def start():
    """Start the web server."""
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start() 