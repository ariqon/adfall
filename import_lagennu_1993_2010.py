#!/usr/bin/env python3
"""Import AD-domar 1993-2010 från lagen.nu och märk källa i databasen."""

import re
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Iterable, Optional

import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DB_PATH = "arbetsdomstolen.db"
BASE_YEAR_URL = "https://lagen.nu/dataset/dv?ad={year}"
USER_AGENT = "Mozilla/5.0 (compatible; adfall-import/1.0)"
TIMEOUT = 40
MAX_WORKERS = 10
RETRIES = 3


@dataclass
class CaseRecord:
    malnummer: str
    datum: str
    titel: str
    url: str
    sammanfattning: str
    refererad: int = 1
    anonymiserad: int = 0
    source_name: str = "lagen.nu"
    source_ref: str = ""


session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})


def fetch(url: str) -> requests.Response:
    last_exc = None
    for attempt in range(1, RETRIES + 1):
        try:
            resp = session.get(url, timeout=TIMEOUT, verify=False)
            resp.raise_for_status()
            return resp
        except Exception as exc:
            last_exc = exc
            if attempt < RETRIES:
                time.sleep(0.4 * attempt)
    raise last_exc


def ensure_source_columns(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(domar)")
    cols = {row[1] for row in cur.fetchall()}

    if "source_name" not in cols:
        cur.execute("ALTER TABLE domar ADD COLUMN source_name TEXT")
    if "source_ref" not in cols:
        cur.execute("ALTER TABLE domar ADD COLUMN source_ref TEXT")

    # Backfill existing rows that already come from arbetsdomstolen.se
    cur.execute(
        """
        UPDATE domar
        SET source_name = 'arbetsdomstolen.se',
            source_ref = COALESCE(source_ref, url)
        WHERE (source_name IS NULL OR trim(source_name) = '')
          AND url LIKE 'https://arbetsdomstolen.se/%'
        """
    )
    conn.commit()


def parse_year_links(year: int) -> list[str]:
    resp = fetch(BASE_YEAR_URL.format(year=year))
    soup = BeautifulSoup(resp.text, "html.parser")

    links: set[str] = set()
    for a in soup.find_all("a", href=True):
        text = a.get_text(" ", strip=True)
        if not re.fullmatch(rf"AD\s+{year}\s+nr\s+\d+", text, flags=re.I):
            continue
        href = a["href"].strip()
        if not href.startswith("http"):
            href = "https://lagen.nu" + href
        links.add(href)

    return sorted(links)


def parse_case(url: str) -> Optional[CaseRecord]:
    resp = fetch(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    h1 = soup.find("h1")
    malnummer = h1.get_text(" ", strip=True) if h1 else ""
    m = re.fullmatch(r"AD\s+\d{4}\s+nr\s+\d+", malnummer)
    if not m:
        return None

    # Metadata table with dt/dd labels
    datum = None
    for dt in soup.find_all("dt"):
        label = dt.get_text(" ", strip=True).lower()
        if "avgörandedatum" in label or "avgorandedatum" in label:
            dd = dt.find_next_sibling("dd")
            if dd:
                datum = dd.get_text(" ", strip=True)
                break

    if not datum or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", datum):
        return None

    lead = soup.select_one("p.lead")
    summary = lead.get_text(" ", strip=True) if lead else ""
    title = summary if summary else malnummer

    return CaseRecord(
        malnummer=malnummer,
        datum=datum,
        titel=title,
        url=url,
        sammanfattning=summary,
        source_ref=url,
    )


def upsert_cases(conn: sqlite3.Connection, records: Iterable[CaseRecord]) -> tuple[int, int]:
    cur = conn.cursor()
    inserted = 0
    updated = 0

    for rec in records:
        cur.execute("SELECT id FROM domar WHERE malnummer = ?", (rec.malnummer,))
        exists = cur.fetchone() is not None

        cur.execute(
            """
            INSERT INTO domar (
                malnummer, datum, titel, url, sammanfattning,
                refererad, anonymiserad, source_name, source_ref
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(malnummer) DO UPDATE SET
                datum = excluded.datum,
                titel = COALESCE(NULLIF(domar.titel, ''), excluded.titel),
                url = COALESCE(NULLIF(domar.url, ''), excluded.url),
                sammanfattning = COALESCE(NULLIF(domar.sammanfattning, ''), excluded.sammanfattning),
                refererad = COALESCE(domar.refererad, excluded.refererad),
                source_name = excluded.source_name,
                source_ref = excluded.source_ref
            """,
            (
                rec.malnummer,
                rec.datum,
                rec.titel,
                rec.url,
                rec.sammanfattning,
                rec.refererad,
                rec.anonymiserad,
                rec.source_name,
                rec.source_ref,
            ),
        )

        if exists:
            updated += 1
        else:
            inserted += 1

    conn.commit()
    return inserted, updated


def run_import(start_year: int = 1993, end_year: int = 2010) -> None:
    print(f"Importerar AD-domar från lagen.nu ({start_year}-{end_year})")

    all_links: list[str] = []
    for year in range(start_year, end_year + 1):
        links = parse_year_links(year)
        print(f"{year}: hittade {len(links)} länkar")
        all_links.extend(links)

    print(f"Totalt länkar att läsa: {len(all_links)}")

    records: list[CaseRecord] = []
    failed = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(parse_case, url): url for url in all_links}
        for i, fut in enumerate(as_completed(futures), 1):
            url = futures[fut]
            try:
                rec = fut.result()
                if rec is None:
                    failed += 1
                else:
                    records.append(rec)
            except Exception:
                failed += 1

            if i % 100 == 0 or i == len(futures):
                print(f"  behandlade {i}/{len(futures)}")

    print(f"Parse OK: {len(records)}, fel: {failed}")

    conn = sqlite3.connect(DB_PATH)
    ensure_source_columns(conn)
    inserted, updated = upsert_cases(conn, records)

    # Final source tagging for existing remaining rows without source_name.
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE domar
        SET source_name = 'okand',
            source_ref = COALESCE(source_ref, url)
        WHERE source_name IS NULL OR trim(source_name) = ''
        """
    )
    conn.commit()

    print(f"Inserterade: {inserted}, uppdaterade: {updated}")

    cur.execute(
        """
        SELECT source_name, COUNT(*)
        FROM domar
        GROUP BY source_name
        ORDER BY COUNT(*) DESC
        """
    )
    print("Källfördelning:")
    for source, cnt in cur.fetchall():
        print(f"  {source}: {cnt}")

    conn.close()


if __name__ == "__main__":
    run_import(1993, 2010)
