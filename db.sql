CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    name TEXT,
    root_path TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE files (
    project_id TEXT,
    path TEXT,
    hash TEXT,
    language TEXT,
    analyzed INTEGER,
    summary TEXT,
    last_analyzed_at TEXT,
    PRIMARY KEY (project_id, path),
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE facts (
    id TEXT PRIMARY KEY,
    project_id TEXT,
    type TEXT,
    source TEXT,
    payload TEXT,
    confidence REAL,
    created_at TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE relations (
    project_id TEXT,
    from_node TEXT,
    to_node TEXT,
    relation TEXT,
    source TEXT,
    PRIMARY KEY (project_id, from_node, to_node, relation),
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
