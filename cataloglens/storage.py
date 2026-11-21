"""Optional SQLite annotation persistence for explicitly configured deployments."""
import json
import sqlite3
import uuid
from pathlib import Path


class AnnotationStore:
    """Append-only decisions with explicit adjudication records."""

    def __init__(self, path):
        self.path = str(path)
        self._uri = self.path == ":memory:"
        if self._uri:
            self.path = f"file:cataloglens-{uuid.uuid4().hex}?mode=memory&cache=shared"
        if self.path != ":memory:":
            Path(self.path).expanduser().parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""CREATE TABLE IF NOT EXISTS annotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_key TEXT NOT NULL,
                item_id TEXT NOT NULL,
                reviewer TEXT NOT NULL,
                label TEXT NOT NULL,
                quality TEXT NOT NULL,
                confidence INTEGER NOT NULL,
                evidence TEXT NOT NULL,
                adjudicated INTEGER NOT NULL DEFAULT 0,
                adjudicator TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")

    def _connect(self):
        return sqlite3.connect(self.path, timeout=10, uri=self._uri)

    def save(self, dataset_key, record):
        with self._connect() as db:
            db.execute("""INSERT INTO annotations
                (dataset_key,item_id,reviewer,label,quality,confidence,evidence)
                VALUES (?,?,?,?,?,?,?)""", (dataset_key, record["item_id"], record["reviewer"],
                record["label"], record["quality"], record["confidence"], record["evidence"]))

    def list(self, dataset_key):
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            return [dict(row) for row in db.execute(
                "SELECT * FROM annotations WHERE dataset_key=? ORDER BY id", (dataset_key,)
            )]

    def adjudicate(self, dataset_key, item_id, adjudicator, label, quality, evidence):
        with self._connect() as db:
            db.execute("""INSERT INTO annotations
                (dataset_key,item_id,reviewer,label,quality,confidence,evidence,adjudicated,adjudicator)
                VALUES (?,?,?,?,?, ?,?,1,?)""", (dataset_key, item_id, adjudicator, label, quality, 5, evidence, adjudicator))


def export_records(rows):
    """Return JSON-safe review records, omitting internal database metadata."""
    fields = ("item_id", "reviewer", "label", "quality", "confidence", "evidence", "adjudicated", "adjudicator")
    return [{key: row[key] for key in fields if key in row} for row in rows]

