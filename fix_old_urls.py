#!/usr/bin/env python3
"""
Fixar URL:er för 2011-2014 och hämtar saknade PDF:er.
"""

import sqlite3
import requests
from bs4 import BeautifulSoup
import os
import time
import re
from urllib.parse import urljoin

DB_PATH = 'arbetsdomstolen.db'
PDF_DIR = 'pdfs'
BASE_URL = 'https://arbetsdomstolen.se'

def get_correct_urls_from_year(year):
    """Hämta korrekta URL:er från årets listningssida."""
    url = f"{BASE_URL}/sv/meddelade-domar/arkiverade-domar/{year}/"
    print(f"Hämtar URL:er för {year}...")

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        urls = {}
        # Hitta alla länkar till domar
        for link in soup.find_all('a', href=re.compile(rf'{year}/\d{{4}}-\d{{2}}-\d{{2}}-ad-{year}-nr-\d+')):
            href = link['href']
            full_url = urljoin(BASE_URL, href)

            # Extrahera målnummer från URL
            match = re.search(rf'ad-{year}-nr-(\d+)', href)
            if match:
                case_num = int(match.group(1))
                malnummer = f"AD {year} nr {case_num}"
                urls[malnummer] = full_url

        print(f"  Hittade {len(urls)} URL:er")
        return urls

    except Exception as e:
        print(f"  Fel: {e}")
        return {}

def update_urls_in_db(year_urls):
    """Uppdatera URL:er i databasen."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    updated = 0
    for malnummer, url in year_urls.items():
        cursor.execute("""
            UPDATE domar SET url = ? WHERE malnummer = ?
        """, (url, malnummer))
        if cursor.rowcount > 0:
            updated += 1

    conn.commit()
    conn.close()
    return updated

def fetch_case_details(url):
    """Hämta detaljer från en dom-sida."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        details = {
            'sammanfattning': None,
            'parter': None,
            'lagrum': None,
            'rattsfragor': None,
            'domslut': None,
            'pdf_url': None
        }

        # Hitta PDF-länk
        pdf_link = soup.find('a', href=re.compile(r'\.pdf$', re.I))
        if pdf_link:
            details['pdf_url'] = urljoin(BASE_URL, pdf_link['href'])

        # Extrahera detaljer från sidan
        article = soup.find('article') or soup.find('main') or soup.find('div', class_=re.compile(r'content', re.I))

        if article:
            paragraphs = article.find_all('p')
            if paragraphs:
                text_parts = [p.get_text(strip=True) for p in paragraphs[:5]]
                details['sammanfattning'] = ' '.join(text_parts)

        return details

    except Exception as e:
        return None

def download_pdf(pdf_url, malnummer):
    """Ladda ner PDF och returnera filsökvägen."""
    try:
        safe_name = re.sub(r'[^\w\-]', '_', malnummer)
        filename = f"{safe_name}.pdf"
        filepath = os.path.join(PDF_DIR, filename)

        if os.path.exists(filepath):
            return filepath

        response = requests.get(pdf_url, timeout=60)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            f.write(response.content)

        return filepath

    except Exception as e:
        print(f"    PDF-fel: {e}")
        return None

def fetch_missing_cases():
    """Hämta detaljer för alla domar som saknar PDF."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, malnummer, url
        FROM domar
        WHERE refererad = 1
        AND url IS NOT NULL
        AND (pdf_path IS NULL OR pdf_path = '')
        ORDER BY datum
    """)
    cases = cursor.fetchall()
    conn.close()

    total = len(cases)
    print(f"\nHämtar detaljer för {total} saknade domar...")
    print("-" * 60)

    success_count = 0
    pdf_count = 0

    for i, (case_id, malnummer, url) in enumerate(cases, 1):
        print(f"[{i}/{total}] {malnummer}...", end=" ", flush=True)

        details = fetch_case_details(url)

        if details:
            pdf_path = None

            if details.get('pdf_url'):
                pdf_path = download_pdf(details['pdf_url'], malnummer)
                if pdf_path:
                    pdf_count += 1
                    print("PDF ✓", end=" ")

            # Uppdatera databasen
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE domar SET
                    sammanfattning = COALESCE(?, sammanfattning),
                    parter = COALESCE(?, parter),
                    lagrum = COALESCE(?, lagrum),
                    rattsfragor = COALESCE(?, rattsfragor),
                    domslut = COALESCE(?, domslut),
                    pdf_path = ?
                WHERE id = ?
            """, (
                details.get('sammanfattning'),
                details.get('parter'),
                details.get('lagrum'),
                details.get('rattsfragor'),
                details.get('domslut'),
                pdf_path,
                case_id
            ))
            conn.commit()
            conn.close()

            success_count += 1
            print("OK")
        else:
            print("FEL")

        time.sleep(0.3)

    return success_count, pdf_count

def main():
    os.makedirs(PDF_DIR, exist_ok=True)

    # Steg 1: Fixa URL:er för 2011-2014
    print("=" * 60)
    print("STEG 1: Fixar URL:er för 2011-2014")
    print("=" * 60)

    total_updated = 0
    for year in [2011, 2012, 2013, 2014]:
        urls = get_correct_urls_from_year(year)
        updated = update_urls_in_db(urls)
        total_updated += updated
        print(f"  Uppdaterade {updated} URL:er för {year}")

    print(f"\nTotalt {total_updated} URL:er fixade.")

    # Steg 2: Hämta saknade detaljer och PDF:er
    print("\n" + "=" * 60)
    print("STEG 2: Hämtar saknade PDF:er")
    print("=" * 60)

    success, pdfs = fetch_missing_cases()

    print("-" * 60)
    print(f"Klart! {success} domar uppdaterade, {pdfs} PDF:er nedladdade.")

    # Statistik
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM domar WHERE pdf_path IS NOT NULL")
    total_pdfs = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM domar WHERE refererad = 1")
    total_ref = cursor.fetchone()[0]
    conn.close()

    print(f"\nTotalt: {total_pdfs}/{total_ref} refererade domar har PDF.")

if __name__ == '__main__':
    main()
