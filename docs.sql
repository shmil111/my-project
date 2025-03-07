-- Documentation Management System

-- Documentation Files Table
CREATE TABLE documentation_files (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    category VARCHAR(100),
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'Active',
    priority INT DEFAULT 3,
    word_count INT DEFAULT 0,
    has_todo BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Documentation Categories
CREATE TABLE doc_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_id INT REFERENCES doc_categories(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Documentation Links
CREATE TABLE doc_links (
    id SERIAL PRIMARY KEY,
    source_doc_id INT REFERENCES documentation_files(id),
    target_doc_id INT REFERENCES documentation_files(id),
    link_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Documentation TODOs
CREATE TABLE doc_todos (
    id SERIAL PRIMARY KEY,
    doc_id INT REFERENCES documentation_files(id),
    task_description TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'Pending',
    priority INT DEFAULT 3,
    due_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Documentation Updates
CREATE TABLE doc_updates (
    id SERIAL PRIMARY KEY,
    doc_id INT REFERENCES documentation_files(id),
    update_description TEXT NOT NULL,
    updated_by VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Initial Category Data
INSERT INTO doc_categories (name, description) VALUES
('System', 'Core system documentation'),
('Implementation', 'Implementation guides and details'),
('API', 'API documentation and references'),
('Security', 'Security-related documentation'),
('User Guides', 'End-user documentation');

-- Initial Documentation Files
INSERT INTO documentation_files (filename, title, category) VALUES
('README.md', 'Project Overview', 'System'),
('todo.md', 'Project Tasks and Status', 'System'),
('implementationguide.md', 'Implementation Guide', 'Implementation'),
('windowsguide.md', 'Windows Setup Guide', 'Implementation'),
('woodenghostguide.md', 'WoodenGhost Integration Guide', 'Implementation'),
('updateguide.md', 'Update System Guide', 'Implementation'),
('apistatusdashboard.md', 'API Status Dashboard', 'API'),
('deepwebresearchimplementation.md', 'Deep Web Research Implementation', 'Implementation'),
('implementationsummary.md', 'Implementation Summary', 'Implementation');

-- Views

-- Active Documentation View
CREATE VIEW active_docs AS
SELECT 
    df.filename,
    df.title,
    dc.name as category,
    df.last_modified,
    df.status,
    COUNT(dt.id) as todo_count
FROM documentation_files df
LEFT JOIN doc_categories dc ON df.category = dc.name
LEFT JOIN doc_todos dt ON df.id = dt.doc_id
WHERE df.status = 'Active'
GROUP BY df.id, df.filename, df.title, dc.name, df.last_modified, df.status;

-- Documentation Dependencies View
CREATE VIEW doc_dependencies AS
SELECT 
    df1.filename as source_doc,
    df2.filename as target_doc,
    dl.link_type
FROM doc_links dl
JOIN documentation_files df1 ON dl.source_doc_id = df1.id
JOIN documentation_files df2 ON dl.target_doc_id = df2.id;

-- Documentation TODOs View
CREATE VIEW pending_todos AS
SELECT 
    df.filename,
    dt.task_description,
    dt.status,
    dt.priority,
    dt.due_date
FROM doc_todos dt
JOIN documentation_files df ON dt.doc_id = df.id
WHERE dt.status = 'Pending'
ORDER BY dt.priority, dt.due_date;

-- Functions

-- Update Documentation Status
CREATE OR REPLACE FUNCTION update_doc_status(
    p_filename VARCHAR(255),
    p_status VARCHAR(50)
) RETURNS VOID AS $$
BEGIN
    UPDATE documentation_files 
    SET status = p_status,
        last_modified = CURRENT_TIMESTAMP
    WHERE filename = p_filename;
END;
$$ LANGUAGE plpgsql;

-- Add Documentation TODO
CREATE OR REPLACE FUNCTION add_doc_todo(
    p_filename VARCHAR(255),
    p_task TEXT,
    p_priority INT DEFAULT 3,
    p_due_date DATE DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    INSERT INTO doc_todos (doc_id, task_description, priority, due_date)
    SELECT id, p_task, p_priority, p_due_date
    FROM documentation_files
    WHERE filename = p_filename;
END;
$$ LANGUAGE plpgsql;

-- Link Documents
CREATE OR REPLACE FUNCTION link_documents(
    p_source_file VARCHAR(255),
    p_target_file VARCHAR(255),
    p_link_type VARCHAR(50)
) RETURNS VOID AS $$
BEGIN
    INSERT INTO doc_links (source_doc_id, target_doc_id, link_type)
    SELECT s.id, t.id, p_link_type
    FROM documentation_files s, documentation_files t
    WHERE s.filename = p_source_file AND t.filename = p_target_file;
END;
$$ LANGUAGE plpgsql;

-- Indexes
CREATE INDEX idx_docs_filename ON documentation_files(filename);
CREATE INDEX idx_docs_category ON documentation_files(category);
CREATE INDEX idx_docs_status ON documentation_files(status);
CREATE INDEX idx_todos_status ON doc_todos(status);
CREATE INDEX idx_todos_priority ON doc_todos(priority);
CREATE INDEX idx_todos_due_date ON doc_todos(due_date);

-- Example Usage:
-- SELECT * FROM active_docs;
-- SELECT * FROM pending_todos;
-- SELECT * FROM doc_dependencies;
-- SELECT update_doc_status('README.md', 'NeedsUpdate');
-- SELECT add_doc_todo('todo.md', 'Update implementation section', 1, '2024-03-14');
-- SELECT link_documents('implementationguide.md', 'apistatusdashboard.md', 'references'); 