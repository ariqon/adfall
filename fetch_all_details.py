#!/usr/bin/env python3
"""
Hämtar sammanfattningar och PDF:er för alla refererade domar från Arbetsdomstolen.
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

def get_cases_to_fetch():
    """Hämta alla refererade domar som behöver uppdateras."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Hämta alla refererade domar som inte har PDF ännu
    cursor.execute("""
        SELECT id, malnummer, url
        FROM domar
        WHERE refererad = 1
        AND url IS NOT NULL
        AND (pdf_path IS NULL OR pdf_path = '')
        ORDER BY datum DESC
    """)
    cases = cursor.fetchall()
    conn.close()
    return cases

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

        # Hitta sammanfattning - leta efter rätt sektion
        # Struktur varierar, så vi testar flera metoder

        # Metod 1: Leta efter rubrik "Sammanfattning" följt av text
        for header in soup.find_all(['h2', 'h3', 'h4', 'strong']):
            text = header.get_text(strip=True).lower()
            if 'sammanfattning' in text:
                # Hämta nästa sibling eller parent's text
                next_elem = header.find_next_sibling()
                if next_elem:
                    details['sammanfattning'] = next_elem.get_text(strip=True)
                    break

        # Metod 2: Leta efter div med klass som innehåller summary
        if not details['sammanfattning']:
            summary_div = soup.find('div', class_=re.compile(r'summary|sammanfattning', re.I))
            if summary_div:
                details['sammanfattning'] = summary_div.get_text(strip=True)

        # Leta efter parter
        for header in soup.find_all(['h2', 'h3', 'h4', 'strong', 'dt']):
            text = header.get_text(strip=True).lower()
            if 'parter' in text or 'part' in text:
                next_elem = header.find_next_sibling()
                if next_elem:
                    details['parter'] = next_elem.get_text(strip=True)
                    break

        # Leta efter lagrum
        for header in soup.find_all(['h2', 'h3', 'h4', 'strong', 'dt']):
            text = header.get_text(strip=True).lower()
            if 'lagrum' in text:
                next_elem = header.find_next_sibling()
                if next_elem:
                    details['lagrum'] = next_elem.get_text(strip=True)
                    break

        # Leta efter rättsfrågor/sökord
        for header in soup.find_all(['h2', 'h3', 'h4', 'strong', 'dt']):
            text = header.get_text(strip=True).lower()
            if 'rättsfråg' in text or 'sökord' in text:
                next_elem = header.find_next_sibling()
                if next_elem:
                    details['rattsfragor'] = next_elem.get_text(strip=True)
                    break

        # Försök hitta mer innehåll via article eller main content
        article = soup.find('article') or soup.find('main') or soup.find('div', class_=re.compile(r'content', re.I))
        if article:
            # Extrahera all text om vi inte hittat sammanfattning
            if not details['sammanfattning']:
                paragraphs = article.find_all('p')
                if paragraphs:
                    # Ta de första paragraferna som sammanfattning
                    text_parts = [p.get_text(strip=True) for p in paragraphs[:5]]
                    details['sammanfattning'] = ' '.join(text_parts)

        return details

    except Exception as e:
        print(f"  Fel vid hämtning av {url}: {e}")
        return None

def download_pdf(pdf_url, malnummer):
    """Ladda ner PDF och returnera filsökvägen."""
    try:
        # Skapa filnamn från målnummer
        safe_name = re.sub(r'[^\w\-]', '_', malnummer)
        filename = f"{safe_name}.pdf"
        filepath = os.path.join(PDF_DIR, filename)

        # Hoppa över om filen redan finns
        if os.path.exists(filepath):
            return filepath

        response = requests.get(pdf_url, timeout=60)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            f.write(response.content)

        return filepath

    except Exception as e:
        print(f"  Fel vid nedladdning av PDF: {e}")
        return None

def update_case(case_id, details, pdf_path):
    """Uppdatera databasen med hämtade detaljer."""
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

def main():
    # Skapa PDF-mapp om den inte finns
    os.makedirs(PDF_DIR, exist_ok=True)

    cases = get_cases_to_fetch()
    total = len(cases)

    print(f"Hämtar detaljer och PDF:er för {total} refererade domar...")
    print("-" * 60)

    success_count = 0
    pdf_count = 0

    for i, (case_id, malnummer, url) in enumerate(cases, 1):
        print(f"[{i}/{total}] {malnummer}...", end=" ", flush=True)

        # Hämta sidans detaljer
        details = fetch_case_details(url)

        if details:
            pdf_path = None

            # Ladda ner PDF om länk hittades
            if details.get('pdf_url'):
                pdf_path = download_pdf(details['pdf_url'], malnummer)
                if pdf_path:
                    pdf_count += 1
                    print(f"PDF ✓", end=" ")

            # Uppdatera databasen
            update_case(case_id, details, pdf_path)
            success_count += 1
            print("OK")
        else:
            print("FEL")

        # Lite paus för att inte överbelasta servern
        time.sleep(0.3)

    print("-" * 60)
    print(f"Klart! {success_count}/{total} domar uppdaterade, {pdf_count} PDF:er nedladdade.")

    # Statistik
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM domar WHERE pdf_path IS NOT NULL")
    total_pdfs = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM domar WHERE sammanfattning IS NOT NULL")
    total_summaries = cursor.fetchone()[0]
    conn.close()

    print(f"\nTotalt i databasen:")
    print(f"  - {total_pdfs} domar med PDF")
    print(f"  - {total_summaries} domar med sammanfattning")

if __name__ == '__main__':
    main()
