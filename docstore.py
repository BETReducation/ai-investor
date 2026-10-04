"""A whole-document JSON store: one Postgres row (locked for writes) or a local
file when there's no DATABASE_URL. For small, low-write data like the partner
chat and the notification feed, where several relational tables would be
overkill."""
import json
import os
import threading
from contextlib import contextmanager


class DocStore:
    def __init__(self, name: str, empty):
        self.table = name
        self.file = os.path.join(os.path.dirname(__file__), f"{name}.json")
        self.empty = empty
        self.db_conn = None
        self.use_db = False
        self._lock = threading.Lock()

    def init(self, db_conn, database_url: str) -> None:
        self.db_conn, self.use_db = db_conn, bool(database_url)
        if self.use_db:
            with db_conn() as conn, conn.cursor() as cur:
                cur.execute(f"CREATE TABLE IF NOT EXISTS {self.table} (id INT PRIMARY KEY, doc JSONB NOT NULL)")
                cur.execute(f"INSERT INTO {self.table} (id, doc) VALUES (1, %s) ON CONFLICT (id) DO NOTHING",
                            (json.dumps(self.empty()),))

    @staticmethod
    def _decode(raw):
        return raw if isinstance(raw, dict) else json.loads(raw)

    @contextmanager
    def txn(self):
        """Yields the document; persists it on clean exit, discards it on exception."""
        if self.use_db:
            conn = self.db_conn()
            try:
                with conn, conn.cursor() as cur:
                    cur.execute(f"SELECT doc FROM {self.table} WHERE id = 1 FOR UPDATE")
                    doc = self._decode(cur.fetchone()[0])
                    yield doc
                    cur.execute(f"UPDATE {self.table} SET doc = %s WHERE id = 1", (json.dumps(doc),))
            finally:
                conn.close()
            return
        with self._lock:
            doc = self.read()
            yield doc
            with open(self.file, "w") as f:
                json.dump(doc, f, indent=2)

    def read(self) -> dict:
        if self.use_db:
            with self.db_conn() as conn, conn.cursor() as cur:
                cur.execute(f"SELECT doc FROM {self.table} WHERE id = 1")
                return self._decode(cur.fetchone()[0])
        if os.path.exists(self.file):
            with open(self.file) as f:
                return json.load(f)
        return self.empty()
