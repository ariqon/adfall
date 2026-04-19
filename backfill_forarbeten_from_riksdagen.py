#!/usr/bin/env python3
"""Fyller saknade förarbeten (från lagen.nu-referenser) via Riksdagens öppna data."""

import re
import sqlite3
import time
from collections import defaultdict
from typing import Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DB_PATH = "arbetsdomstolen.db"
BASE_LAGNU = "https://lagen.nu"
BASE_RDK = "https://data.riksdagen.se"
TIMEOUT = 40

TARGET_SFS = [
    "1974:371",
    "1976:580",
    "1977:480",
    "1982:673",
    "1982:80",
    "1994:260",
    "2021:890",
]

FORARBETE_PATH_PREFIXES = ("/prop/", "/sou/", "/ds/", "/dir/", "/bet/", "/rskr/")

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; adfall-riksdagen-backfill/1.0)"})


def get(url: str, retries: int = 3) -> requests.Response:
    last = None
    for attempt in range(1, retries + 1):
        try:
            r = session.get(url, timeout=TIMEOUT, verify=False)
            r.raise_for_status()
            return r
        except Exception as exc:
            last = exc
            if attempt < retries:
                time.sleep(0.3 * attempt)
    raise last


def extract_law_refs() -> dict[str, set[str]]:
    refs_by_law: dict[str, set[str]] = {sfs: set() for sfs in TARGET_SFS}
    for sfs in TARGET_SFS:
        html = get(f"{BASE_LAGNU}/{sfs}").text
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            full = urljoin(BASE_LAGNU, a["href"].strip())
            p = urlparse(full)
            if p.path.startswith(FORARBETE_PATH_PREFIXES):
                refs_by_law[sfs].add(p.path.strip("/"))
    return refs_by_law


def load_existing_doc_ids(conn: sqlite3.Connection) -> set[str]:
    cur = conn.cursor()
    cur.execute("SELECT doc_id FROM forarbeten")
    return {row[0] for row in cur.fetchall()}


def fetch_prop_from_riksdagen(rm: str, number: int) -> Optional[Tuple[str, str, str]]:
    """Returnerar (title, html_url, fulltext) för proposition rm:number."""
    # hämta alla propositioner för riksmötet i ett svep och filtrera exakt på nummer
    api = f"{BASE_RDK}/dokumentlista/?doktyp=prop&rm={rm}&utformat=json&sz=4000"
    data = get(api).json()
    docs = data.get("dokumentlista", {}).get("dokument", [])
    if isinstance(docs, dict):
        docs = [docs]

    target = None
    for d in docs:
        try:
            if str(d.get("rm", "")).strip() != rm:
                continue
            n = int(str(d.get("nummer", "")).strip())
            if n == number:
                target = d
                break
        except Exception:
            continue

    if not target:
        return None

    title = (target.get("titel") or "").strip()
    html_url = (target.get("dokument_url_html") or "").strip()
    text_url = (target.get("dokument_url_text") or "").strip()

    if html_url.startswith("//"):
        html_url = "https:" + html_url
    elif html_url and html_url.startswith("/"):
        html_url = BASE_RDK + html_url

    if text_url.startswith("//"):
        text_url = "https:" + text_url
    elif text_url and text_url.startswith("/"):
        text_url = BASE_RDK + text_url

    fulltext = ""
    if text_url:
        fulltext = get(text_url).text

    return title, html_url, fulltext


def upsert_forarbete(conn: sqlite3.Connection, doc_id: str, title: str, url: str, fulltext: str, source_ref: str) -> None:
    conn.execute(
        """
        INSERT INTO forarbeten (doc_id, doc_type, title, url, fulltext, source_name, source_ref, updated_at)
        VALUES (?, 'prop', ?, ?, ?, 'riksdagen.se', ?, CURRENT_TIMESTAMP)
        ON CONFLICT(doc_id) DO UPDATE SET
            doc_type='prop',
            title=excluded.title,
            url=excluded.url,
            fulltext=excluded.fulltext,
            source_name='riksdagen.se',
            source_ref=excluded.source_ref,
            updated_at=CURRENT_TIMESTAMP
        """,
        (doc_id, title or doc_id, url or source_ref, fulltext or "", source_ref),
    )


def ensure_law_link(conn: sqlite3.Connection, sfs: str, doc_id: str) -> None:
    conn.execute(
        """
        INSERT INTO law_forarbeten (sfs, doc_id, ref_label, ref_url)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(sfs, doc_id) DO NOTHING
        """,
        (sfs, doc_id, doc_id, f"{BASE_LAGNU}/{doc_id}"),
    )


def main() -> None:
    conn = sqlite3.connect(DB_PATH)

    refs_by_law = extract_law_refs()
    all_refs = set().union(*refs_by_law.values())
    existing = load_existing_doc_ids(conn)
    missing = sorted(all_refs - existing)

    print(f"Saknade förarbeten före backfill: {len(missing)}")

    prop_pattern = re.compile(r"^prop/(\d{4}/\d{2}):(\d+)$")
    unresolved = []
    inserted = 0

    # cache per riksmöte minimalt via helper-funktionens API-anrop (ett per dokument nu);
    # mängden är liten så håll det enkelt.
    for idx, doc_id in enumerate(missing, 1):
        m = prop_pattern.match(doc_id)
        if not m:
            unresolved.append((doc_id, "not_prop"))
            continue

        rm = m.group(1)
        number = int(m.group(2))

        try:
            found = fetch_prop_from_riksdagen(rm, number)
            if not found:
                unresolved.append((doc_id, "not_found_in_api"))
                continue

            title, html_url, fulltext = found
            source_ref = html_url or f"{BASE_RDK}/dokumentlista/?doktyp=prop&rm={rm}&nummer={number}&utformat=json"
            upsert_forarbete(conn, doc_id, title, html_url, fulltext, source_ref)

            # länka till de lagar som refererar doc_id
            for sfs, refs in refs_by_law.items():
                if doc_id in refs:
                    ensure_law_link(conn, sfs, doc_id)

            inserted += 1
        except Exception as exc:
            unresolved.append((doc_id, exc.__class__.__name__))

        if idx % 5 == 0 or idx == len(missing):
            conn.commit()
            print(f"  behandlade {idx}/{len(missing)}")

    conn.commit()

    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM forarbeten")
    fb = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM law_forarbeten")
    links = cur.fetchone()[0]

    print("\nKlart")
    print(f"  importerade via riksdagen: {inserted}")
    print(f"  forarbeten totalt: {fb}")
    print(f"  law_forarbeten totalt: {links}")
    print(f"  kvar olösta: {len(unresolved)}")
    for doc_id, reason in unresolved[:30]:
        print(f"    - {doc_id}: {reason}")

    conn.close()


if __name__ == "__main__":
    main()
