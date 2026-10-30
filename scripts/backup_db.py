"""Export every table in the Railway Postgres database to gzipped JSON-lines files.

Railway's Hobby plan has no scheduled backups, so this runs from Gary's Mac instead.
Connection string: DATABASE_URL in the environment, or in ~/.gcg-backup.env as a
single line `DATABASE_URL=...` (use the Postgres service's public/TCP-proxy URL;
the file lives outside the repo on purpose).

Output: ~/Documents/GCG-Backups/<YYYY-MM-DD>/<table>.jsonl.gz + manifest.json.
The newest KEEP backups are kept (each is ~200MB, mostly alpha_content).
"""
import base64
import datetime as dt
import decimal
import gzip
import json
import os
import shutil
import sys
import time
import uuid
from pathlib import Path

import psycopg2

KEEP = 7
ENV_FILE = Path.home() / ".gcg-backup.env"
BACKUP_ROOT = Path(os.environ.get("GCG_BACKUP_DIR", Path.home() / "Documents" / "GCG-Backups"))


def _database_url():
    url = os.environ.get("DATABASE_URL", "")
    if not url and ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if line.startswith("DATABASE_URL="):
                url = line.split("=", 1)[1].strip().strip('"').strip("'")
    return url


def _encode(value):
    if isinstance(value, (bytes, bytearray, memoryview)):
        return {"__bytes_b64__": base64.b64encode(bytes(value)).decode()}
    if isinstance(value, (dt.datetime, dt.date, dt.time)):
        return value.isoformat()
    if isinstance(value, decimal.Decimal):
        return str(value)
    if isinstance(value, uuid.UUID):
        return str(value)
    raise TypeError(f"cannot serialise {type(value).__name__}")


def dump_table(conn, table, path):
    rows = 0
    with conn.cursor(name=f"dump_{abs(hash(table))}") as cur, gzip.open(path, "wt", encoding="utf-8") as out:
        cur.itersize = 2000
        cur.execute(f'SELECT * FROM "{table}"')
        for row in cur:
            out.write(json.dumps(row, default=_encode) + "\n")
            rows += 1
    return rows


def prune(root, keep=KEEP):
    dated = sorted(p for p in root.iterdir() if p.is_dir() and len(p.name) == 10 and p.name[:4].isdigit())
    for old in dated[:-keep]:
        shutil.rmtree(old, ignore_errors=True)


def _export_all(url, out_dir):
    manifest = {"taken_at": dt.datetime.now(dt.timezone.utc).isoformat(), "tables": {}}
    conn = psycopg2.connect(url, connect_timeout=15)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY 1")
            tables = [r[0] for r in cur.fetchall()]
        conn.commit()
        for table in tables:
            manifest["tables"][table] = dump_table(conn, table, out_dir / f"{table}.jsonl.gz")
            # Release this table's read lock before the next one: holding them all for the whole
            # run deadlocked against the web app's startup schema changes.
            conn.commit()
    finally:
        conn.close()
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def main():
    url = _database_url()
    if not url:
        sys.exit(f"No DATABASE_URL in the environment or {ENV_FILE}")
    day_dir = BACKUP_ROOT / dt.date.today().isoformat()
    tmp_dir = BACKUP_ROOT / (day_dir.name + ".partial")
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, 4):
        shutil.rmtree(tmp_dir, ignore_errors=True)
        tmp_dir.mkdir()
        try:
            manifest = _export_all(url, tmp_dir)
            break
        except psycopg2.Error as exc:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            if attempt == 3:
                raise
            print(f"Attempt {attempt} failed ({type(exc).__name__}), retrying...", file=sys.stderr)
            time.sleep(10 * attempt)
    # Only a complete export replaces today's folder, so a failed run never leaves a half-written backup.
    shutil.rmtree(day_dir, ignore_errors=True)
    tmp_dir.rename(day_dir)
    prune(BACKUP_ROOT)
    print(f"Backed up {len(manifest['tables'])} tables to {day_dir}: {manifest['tables']}")


if __name__ == "__main__":
    main()
