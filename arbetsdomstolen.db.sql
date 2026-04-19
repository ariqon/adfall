-- Arbetsdomstolen domar databas
-- Skapad 2025

CREATE TABLE IF NOT EXISTS domar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    malnummer TEXT UNIQUE NOT NULL,
    datum DATE NOT NULL,
    titel TEXT,
    url TEXT,
    sammanfattning TEXT,
    parter TEXT,
    lagrum TEXT,
    rattsfragor TEXT,
    domslut TEXT,
    refererad BOOLEAN DEFAULT 0,
    anonymiserad BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_datum ON domar(datum);
CREATE INDEX IF NOT EXISTS idx_malnummer ON domar(malnummer);
CREATE INDEX IF NOT EXISTS idx_refererad ON domar(refererad);
