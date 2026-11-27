"""SQLite storage; transactions close their connections, including on errors."""
from contextlib import contextmanager
import sqlite3


class ClosingConnection(sqlite3.Connection):
    # Commit or roll back the transaction and always close the SQLite connection afterward.
    def __exit__(self, *args):
        try:
            return super().__exit__(*args)
        finally:
            self.close()


# Open a self-closing SQLite connection with row access, foreign keys, and a write-lock timeout.
def connect(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=30, factory=ClosingConnection)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 30000")
    return connection


# Create the local person and relationship schema, enable WAL, and add graph-scoped indexes.
def initialize(path):
    with connect(path) as connection:
        connection.execute("PRAGMA journal_mode = WAL")
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS persons (
                graph_id TEXT NOT NULL REFERENCES graphs(id) ON DELETE CASCADE,
                id TEXT NOT NULL,
                alias TEXT,
                nom TEXT,
                prenom TEXT,
                date_naissance TEXT,
                date_mort TEXT,
                age INTEGER,
                entreprise TEXT,
                description TEXT,
                PRIMARY KEY (graph_id, id),
                UNIQUE (graph_id, alias)
            );
            CREATE INDEX IF NOT EXISTS idx_person_company ON persons(graph_id, entreprise);
            CREATE TABLE IF NOT EXISTS relations (
                graph_id TEXT NOT NULL,
                id TEXT NOT NULL,
                source TEXT NOT NULL,
                target TEXT NOT NULL,
                label TEXT NOT NULL,
                properties TEXT NOT NULL DEFAULT '{}',
                PRIMARY KEY (graph_id, id),
                UNIQUE (graph_id, source, target, label),
                CHECK (source <> target),
                FOREIGN KEY (graph_id, source) REFERENCES persons(graph_id, id) ON DELETE CASCADE,
                FOREIGN KEY (graph_id, target) REFERENCES persons(graph_id, id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_relation_target ON relations(graph_id, target);
        """)


class GraphStore:
    # Remember the SQLite database path used by graph transactions.
    def __init__(self, path):
        self.path = path

    # Open a write transaction that commits all graph changes together or rolls them back on failure.
    @contextmanager
    def session(self):
        with connect(self.path) as connection:
            # One transaction for a person change AND its derived company links.
            connection.execute("BEGIN IMMEDIATE")
            yield Transaction(connection)


class Transaction:
    # Wrap an existing SQLite connection for graph operation calls.
    def __init__(self, connection):
        self.connection = connection

    # Run a graph operation on the current connection; writes use the same transaction adapter.
    def execute_read(self, operation, *args):
        return operation(self.connection, *args)

    execute_write = execute_read
