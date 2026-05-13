#!/usr/bin/env python3
"""Create search indexes for the Arbetsdomstolen SQLite database."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("ADFALL_DB_PATH", ROOT / "arbetsdomstolen.db"))


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"Database not found: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(
            """
            DROP TABLE IF EXISTS domar_fts;
            DROP TABLE IF EXISTS laws_fts;
            DROP TABLE IF EXISTS forarbeten_fts;

            CREATE INDEX IF NOT EXISTS idx_domar_datum_malnummer
                ON domar(datum DESC, malnummer DESC);

            CREATE INDEX IF NOT EXISTS idx_domar_refererad_datum
                ON domar(refererad, datum DESC, malnummer DESC);

            CREATE INDEX IF NOT EXISTS idx_domar_anonymiserad_datum
                ON domar(anonymiserad, datum DESC, malnummer DESC);

            CREATE INDEX IF NOT EXISTS idx_forarbeten_doc_type
                ON forarbeten(doc_type);

            CREATE VIRTUAL TABLE IF NOT EXISTS domar_fts USING fts5(
                malnummer,
                titel,
                sammanfattning,
                parter,
                lagrum,
                rattsfragor,
                domslut,
                fulltext,
                content='domar',
                content_rowid='id',
                detail=none,
                tokenize='unicode61 remove_diacritics 2'
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS laws_fts USING fts5(
                sfs,
                title,
                fulltext,
                content='laws',
                content_rowid='rowid',
                detail=none,
                tokenize='unicode61 remove_diacritics 2'
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS forarbeten_fts USING fts5(
                doc_id,
                doc_type,
                title,
                fulltext,
                content='forarbeten',
                content_rowid='rowid',
                detail=none,
                tokenize='unicode61 remove_diacritics 2'
            );

            INSERT INTO domar_fts(domar_fts) VALUES('rebuild');
            INSERT INTO laws_fts(laws_fts) VALUES('rebuild');
            INSERT INTO forarbeten_fts(forarbeten_fts) VALUES('rebuild');

            ANALYZE;
            PRAGMA optimize;
            """
        )

    print(f"Optimized {DB_PATH}")


if __name__ == "__main__":
    main()
