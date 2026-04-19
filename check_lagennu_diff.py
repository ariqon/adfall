#!/usr/bin/env python3
"""Diffar lokal AD-databas mot lagen.nu (dataset/dv?ad=YYYY)."""

import argparse
import re
import sqlite3
from collections import defaultdict

import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def fetch_remote_numbers(year: int, verify_tls: bool) -> set[int]:
    url = f"https://lagen.nu/dataset/dv?ad={year}"
    resp = requests.get(url, timeout=40, verify=verify_tls)
    resp.raise_for_status()
    text = BeautifulSoup(resp.text, "html.parser").get_text("\n", strip=True)
    return {
        int(nr)
        for y, nr in re.findall(r"AD\s+(\d{4})\s+nr\s+(\d+)", text, flags=re.I)
        if int(y) == year
    }


def load_local_numbers(db_path: str, start_year: int, end_year: int) -> dict[int, set[int]]:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT malnummer
        FROM domar
        WHERE substr(malnummer, 4, 4) BETWEEN ? AND ?
        """,
        (str(start_year), str(end_year)),
    )

    by_year: dict[int, set[int]] = defaultdict(set)
    for (malnummer,) in cur.fetchall():
        m = re.fullmatch(r"AD\s+(\d{4})\s+nr\s+(\d+)", (malnummer or "").strip())
        if not m:
            continue
        year = int(m.group(1))
        num = int(m.group(2))
        if start_year <= year <= end_year:
            by_year[year].add(num)

    conn.close()
    return by_year


def main() -> None:
    parser = argparse.ArgumentParser(description="Diffa AD-data i lokal SQLite mot lagen.nu")
    parser.add_argument("--db", default="arbetsdomstolen.db", help="Sökväg till SQLite-databas")
    parser.add_argument("--start", type=int, default=1993, help="Startår")
    parser.add_argument("--end", type=int, default=2023, help="Slutår")
    parser.add_argument(
        "--verify-tls",
        action="store_true",
        help="Verifiera TLS-certifikat (default: av i denna miljö)",
    )
    parser.add_argument(
        "--show-lists",
        action="store_true",
        help="Visa exakta listor med missing/extra per år",
    )
    args = parser.parse_args()

    if args.start > args.end:
        raise SystemExit("--start måste vara <= --end")

    local_by_year = load_local_numbers(args.db, args.start, args.end)

    total_missing = 0
    total_extra = 0

    print("YEAR|REMOTE|LOCAL|MISSING|EXTRA")
    for year in range(args.start, args.end + 1):
        remote = fetch_remote_numbers(year, verify_tls=args.verify_tls)
        local = local_by_year.get(year, set())

        missing = sorted(remote - local)
        extra = sorted(local - remote)

        total_missing += len(missing)
        total_extra += len(extra)

        print(f"{year}|{len(remote)}|{len(local)}|{len(missing)}|{len(extra)}")

        if args.show_lists and (missing or extra):
            if missing:
                print(f"  missing {year}: " + ", ".join(f"AD {year} nr {n}" for n in missing))
            if extra:
                print(f"  extra {year}: " + ", ".join(f"AD {year} nr {n}" for n in extra))

    print(f"TOTAL|missing={total_missing}|extra={total_extra}")


if __name__ == "__main__":
    main()
