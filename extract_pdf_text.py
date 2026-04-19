#!/usr/bin/env python3
"""
Extraherar text från alla PDF:er och sparar i databasen.
"""

import sqlite3
import pdfplumber
import os

DB_PATH = 'arbetsdomstolen.db'
PDF_DIR = 'pdfs'

def extract_text_from_pdf(pdf_path):
    """Extrahera all text från en PDF."""
    try:
        text_parts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return '\n\n'.join(text_parts)
    except Exception as e:
        print(f"    Fel: {e}")
        return None

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Hämta alla domar med PDF som inte har fulltext ännu
    cursor.execute("""
        SELECT id, malnummer, pdf_path
        FROM domar
        WHERE pdf_path IS NOT NULL
        AND (fulltext IS NULL OR fulltext = '')
        ORDER BY datum DESC
    """)
    cases = cursor.fetchall()

    total = len(cases)
    print(f"Extraherar text från {total} PDF:er...")
    print("-" * 60)

    success_count = 0
    total_chars = 0

    for i, (case_id, malnummer, pdf_path) in enumerate(cases, 1):
        print(f"[{i}/{total}] {malnummer}...", end=" ", flush=True)

        if not os.path.exists(pdf_path):
            print("Fil saknas")
            continue

        text = extract_text_from_pdf(pdf_path)

        if text:
            cursor.execute("UPDATE domar SET fulltext = ? WHERE id = ?", (text, case_id))
            conn.commit()
            chars = len(text)
            total_chars += chars
            success_count += 1
            print(f"OK ({chars:,} tecken)")
        else:
            print("Kunde inte extrahera text")

    conn.close()

    print("-" * 60)
    print(f"Klart! {success_count}/{total} PDF:er extraherade.")
    print(f"Totalt {total_chars:,} tecken ({total_chars/1000000:.1f} MB text)")

    # Statistik
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM domar WHERE fulltext IS NOT NULL AND fulltext != ''")
    with_text = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(LENGTH(fulltext)) FROM domar WHERE fulltext IS NOT NULL")
    total_size = cursor.fetchone()[0] or 0
    conn.close()

    print(f"\nI databasen: {with_text} domar med fulltext ({total_size/1000000:.1f} MB)")

if __name__ == '__main__':
    main()
