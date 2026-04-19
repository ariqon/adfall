#!/usr/bin/env python3
"""Importerar utvalda lagar och relevanta förarbeten från lagen.nu."""

import re
import sqlite3
import time
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DB_PATH = "arbetsdomstolen.db"
BASE_URL = "https://lagen.nu"
TIMEOUT = 40
RETRIES = 3

# Exakt urval från användaren (dubblett hanteras nedan)
TARGET_SFS = [
    "1976:580",
    "1982:80",
    "1974:371",
    "1977:480",
    "1977:480",
    "1982:673",
    "1994:260",
    "2021:890",
]

FORARBETE_PATH_PREFIXES = ("/prop/", "/sou/", "/ds/", "/dir/", "/bet/", "/rskr/")


@dataclass
class LawDoc:
    sfs: str
    title: str
    url: str
    fulltext: str


session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; adfall-laws-import/1.0)"})


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


def ensure_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS laws (
            sfs TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            fulltext TEXT,
            source_name TEXT NOT NULL,
            source_ref TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS forarbeten (
            doc_id TEXT PRIMARY KEY,
            doc_type TEXT,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            fulltext TEXT,
            source_name TEXT NOT NULL,
            source_ref TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS law_forarbeten (
            sfs TEXT NOT NULL,
            doc_id TEXT NOT NULL,
            ref_label TEXT,
            ref_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (sfs, doc_id),
            FOREIGN KEY (sfs) REFERENCES laws(sfs),
            FOREIGN KEY (doc_id) REFERENCES forarbeten(doc_id)
        )
        """
    )

    cur.execute("CREATE INDEX IF NOT EXISTS idx_law_forarbeten_sfs ON law_forarbeten(sfs)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_law_forarbeten_doc ON law_forarbeten(doc_id)")
    conn.commit()


def normalize_title(text: str) -> str:
    t = (text or "").strip()
    t = re.sub(r"\s+\|\s*Lagen\.nu\s*$", "", t, flags=re.I)
    return re.sub(r"\s+", " ", t)


def parse_law_page(sfs: str) -> tuple[LawDoc, list[tuple[str, str, str]]]:
    url = f"{BASE_URL}/{sfs}"
    resp = fetch(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    h1 = soup.find("h1")
    title = normalize_title(h1.get_text(" ", strip=True) if h1 else (soup.title.get_text(" ", strip=True) if soup.title else sfs))

    article = soup.find("article")
    fulltext = article.get_text("\n", strip=True) if article else soup.get_text("\n", strip=True)

    refs: list[tuple[str, str, str]] = []
    seen_docs: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        full_href = urljoin(BASE_URL, href)
        parsed = urlparse(full_href)

        # Förarbete-länkar i lagen.nu
        if not parsed.path.startswith(FORARBETE_PATH_PREFIXES):
            continue

        # doc_id utan fragment/query, t.ex. prop/2018/19:105
        doc_id = parsed.path.strip("/")
        if not doc_id or doc_id in seen_docs:
            continue

        seen_docs.add(doc_id)
        label = re.sub(r"\s+", " ", a.get_text(" ", strip=True))
        refs.append((doc_id, label, full_href))

    return LawDoc(sfs=sfs, title=title, url=url, fulltext=fulltext), refs


def parse_forarbete(doc_id: str) -> tuple[str, str, str, str]:
    """Returnerar (doc_type, title, url, fulltext)."""
    url = f"{BASE_URL}/{doc_id}"
    resp = fetch(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    doc_type = doc_id.split("/", 1)[0]
    title = normalize_title(soup.title.get_text(" ", strip=True) if soup.title else doc_id)

    article = soup.find("article")
    fulltext = article.get_text("\n", strip=True) if article else soup.get_text("\n", strip=True)

    return doc_type, title, url, fulltext


def upsert_law(conn: sqlite3.Connection, law: LawDoc) -> None:
    conn.execute(
        """
        INSERT INTO laws (sfs, title, url, fulltext, source_name, source_ref, updated_at)
        VALUES (?, ?, ?, ?, 'lagen.nu', ?, CURRENT_TIMESTAMP)
        ON CONFLICT(sfs) DO UPDATE SET
            title=excluded.title,
            url=excluded.url,
            fulltext=excluded.fulltext,
            source_name=excluded.source_name,
            source_ref=excluded.source_ref,
            updated_at=CURRENT_TIMESTAMP
        """,
        (law.sfs, law.title, law.url, law.fulltext, law.url),
    )


def upsert_forarbete(conn: sqlite3.Connection, doc_id: str, doc_type: str, title: str, url: str, fulltext: str) -> None:
    conn.execute(
        """
        INSERT INTO forarbeten (doc_id, doc_type, title, url, fulltext, source_name, source_ref, updated_at)
        VALUES (?, ?, ?, ?, ?, 'lagen.nu', ?, CURRENT_TIMESTAMP)
        ON CONFLICT(doc_id) DO UPDATE SET
            doc_type=excluded.doc_type,
            title=excluded.title,
            url=excluded.url,
            fulltext=excluded.fulltext,
            source_name=excluded.source_name,
            source_ref=excluded.source_ref,
            updated_at=CURRENT_TIMESTAMP
        """,
        (doc_id, doc_type, title, url, fulltext, url),
    )


def upsert_law_link(conn: sqlite3.Connection, sfs: str, doc_id: str, label: str, ref_url: str) -> None:
    conn.execute(
        """
        INSERT INTO law_forarbeten (sfs, doc_id, ref_label, ref_url)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(sfs, doc_id) DO UPDATE SET
            ref_label=excluded.ref_label,
            ref_url=excluded.ref_url
        """,
        (sfs, doc_id, label, ref_url),
    )


def main() -> None:
    # Deduplicera men behåll ordning
    sfs_list = list(dict.fromkeys(TARGET_SFS))

    conn = sqlite3.connect(DB_PATH)
    ensure_schema(conn)

    all_doc_ids: set[str] = set()
    law_refs: dict[str, list[tuple[str, str, str]]] = {}

    print(f"Importerar {len(sfs_list)} lagar...")
    for sfs in sfs_list:
        law, refs = parse_law_page(sfs)
        upsert_law(conn, law)
        law_refs[sfs] = refs
        for doc_id, _, _ in refs:
            all_doc_ids.add(doc_id)
        conn.commit()
        print(f"  {sfs}: lagtext OK, forarbetsreferenser={len(refs)}")

    print(f"\nUnika förarbeten att läsa: {len(all_doc_ids)}")

    skipped: list[str] = []
    for i, doc_id in enumerate(sorted(all_doc_ids), 1):
        try:
            doc_type, title, url, fulltext = parse_forarbete(doc_id)
            upsert_forarbete(conn, doc_id, doc_type, title, url, fulltext)
        except requests.HTTPError as exc:
            status = getattr(exc.response, "status_code", None)
            # Some historical references on lagen.nu are dead links; skip those.
            skipped.append(f"{doc_id} (HTTP {status})")
        except Exception as exc:
            skipped.append(f"{doc_id} ({exc.__class__.__name__})")

        if i % 25 == 0 or i == len(all_doc_ids):
            conn.commit()
            print(f"  behandlade {i}/{len(all_doc_ids)}")

    # länktabell
    cur = conn.cursor()
    for sfs, refs in law_refs.items():
        for doc_id, label, ref_url in refs:
            cur.execute("SELECT 1 FROM forarbeten WHERE doc_id = ?", (doc_id,))
            if cur.fetchone():
                upsert_law_link(conn, sfs, doc_id, label, ref_url)

    conn.commit()

    # verifiering
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM laws")
    laws_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM forarbeten")
    fb_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM law_forarbeten")
    links_count = cur.fetchone()[0]

    print("\nKlart.")
    print(f"  laws: {laws_count}")
    print(f"  forarbeten: {fb_count}")
    print(f"  law_forarbeten: {links_count}")
    if skipped:
        print(f"  hoppade över {len(skipped)} otillgängliga förarbeten")
        for item in skipped[:20]:
            print(f"    - {item}")

    conn.close()


if __name__ == "__main__":
    main()
