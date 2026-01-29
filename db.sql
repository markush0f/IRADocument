-- =============================================================================
-- DATABASE SCHEMA - IRADocument
-- =============================================================================
-- This file documents the SQLite database structure used for 
-- automatic repository analysis and documentation.
-- =============================================================================

-- TABLE: projects
-- Stores the metadata of the projects (repositories) being analyzed.
-- This is the root entity for all other data.
CREATE TABLE projects (
    id TEXT PRIMARY KEY,        -- Unique project identifier (e.g., UUID or slug)
    name TEXT,                  -- Human-readable project name
    root_path TEXT,             -- Absolute or relative path in the filesystem
    created_at TEXT,            -- Project registration date (ISO 8601)
    updated_at TEXT             -- Last time the project metadata was updated
);

-- TABLE: files
-- Stores the inventory of files detected within a project.
-- Tracks which files have been analyzed by the LLM.
CREATE TABLE files (
    project_id TEXT,            -- Reference to the project
    path TEXT,                  -- Relative path of the file within the project
    hash TEXT,                  -- Content hash for change detection (optional)
    language TEXT,              -- Detected programming language (e.g., python, javascript)
    analyzed INTEGER DEFAULT 0, -- Flag (0/1) indicating if the LLM has processed this file
    summary TEXT,               -- AI-generated summary of the file's purpose
    last_analyzed_at TEXT,      -- Timestamp of the last analysis
    PRIMARY KEY (project_id, path),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- TABLE: facts
-- Alstores atomic discoveries or findings about the project.
-- Used for frameworks, specific technologies, databases, configurations, etc.
CREATE TABLE facts (
    id TEXT PRIMARY KEY,        -- Unique identifier for the fact (UUID)
    project_id TEXT,            -- Reference to the project
    type TEXT,                  -- Category of the discovery (e.g., 'framework', 'library', 'db')
    source TEXT,                -- Origin of the finding (e.g., 'package.json', 'file_analysis')
    payload TEXT,               -- JSON containing extra details (e.g., {"name": "FastAPI", "version": "0.100"})
    confidence REAL,            -- AI or scanner certainty level (0.0 to 1.0)
    created_at TEXT,            -- Date the fact was registered
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- TABLE: relations
-- Stores architectural dependencies and flows between system components.
-- Enables the construction of an architecture graph (e.g., 'Module A' -> calls -> 'API B').
CREATE TABLE relations (
    project_id TEXT,            -- Reference to the project
    from_node TEXT,             -- Origin point (e.g., a file, class, or service)
    to_node TEXT,               -- Destination point
    relation TEXT,              -- Type of relationship (e.g., 'calls', 'imports', 'depends_on')
    source TEXT,                -- Origin where the relation was detected
    PRIMARY KEY (project_id, from_node, to_node, relation),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- TABLE: tree_nodes
-- Stores the traversal state for the "Living Tree" strategy.
-- Tracks priority, status, and depth of each node in the exploration graph.
CREATE TABLE tree_nodes (
    project_id TEXT,            -- Reference to the project
    path TEXT,                  -- Relative path of the file or node
    priority TEXT DEFAULT 'medium', -- Analysis priority: 'high', 'medium', 'low', 'skip'
    status TEXT DEFAULT 'pending',  -- Process status: 'pending', 'analyzing', 'done', 'error'
    reason TEXT,                -- Why this node is being analyzed (e.g., "Imported by main.py")
    depth INTEGER DEFAULT 0,    -- Depth from the seed (entry point)
    created_at TEXT,            -- Creation timestamp
    updated_at TEXT,            -- Last update timestamp
    PRIMARY KEY (project_id, path),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
