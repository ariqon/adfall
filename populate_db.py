#!/usr/bin/env python3
"""Fyller arbetsdomstolen.db med domar från 2025."""

import sqlite3

# Alla domar från 2025
domar = [
    ("AD 2025 nr 1", "2025-01-22", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-01-22-ad-2025-nr-1/", False, False),
    ("AD 2025 nr 2", "2025-01-23", "Blockad mot krigsmateriel - interimistisk prövning", "/sv/meddelade-domar/arkiverade-domar/2025/2025-01-23-ad-2025-nr-2/", True, False),
    ("AD 2025 nr 3", "2025-02-03", "Politisk stridsåtgärd - blockad mot Israel", "/sv/meddelade-domar/arkiverade-domar/2025/2025-02-03-ad-2025-nr-3/", True, False),
    ("AD 2025 nr 4", "2025-02-03", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-02-03-ad-2025-nr-4/", False, False),
    ("AD 2025 nr 5", "2025-02-07", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-02-07-ad-2025-nr-5/", False, False),
    ("AD 2025 nr 6", "2025-02-19", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-02-19-ad-2025-nr-6/", False, True),
    ("AD 2025 nr 7", "2025-02-19", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-02-19-ad-2025-nr-7/", False, False),
    ("AD 2025 nr 8", "2025-02-21", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-02-21-ad-2025-nr-8/", False, False),
    ("AD 2025 nr 9", "2025-02-28", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-02-28-ad-2025-nr-9/", False, False),
    ("AD 2025 nr 10", "2025-03-05", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-03-05-ad-2025-nr-10/", False, False),
    ("AD 2025 nr 11", "2025-03-06", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-03-06-ad-2025-nr-11/", False, False),
    ("AD 2025 nr 12", "2025-03-12", "Polisassistent - dataintrång och avskedande", "/sv/meddelade-domar/arkiverade-domar/2025/2025-03-12-ad-2025-nr-12/", True, False),
    ("AD 2025 nr 13", "2025-03-17", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-03-17-ad-2025-nr-13/", False, False),
    ("AD 2025 nr 14", "2025-03-24", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-03-24-ad-2024-nr-14/", False, False),
    ("AD 2025 nr 15", "2025-03-26", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-03-26-ad-2025-nr-15/", False, False),
    ("AD 2025 nr 16", "2025-03-28", "Helikopterpiloter - pensionsålder fastställelse", "/sv/meddelade-domar/arkiverade-domar/2025/2025-03-28-ad-2025-nr-16/", True, False),
    ("AD 2025 nr 17", "2025-04-02", "Trafikvakt - byggavtal tillämpning", "/sv/meddelade-domar/arkiverade-domar/2025/2025-04-02-ad-2025-nr-17/", True, False),
    ("AD 2025 nr 18", "2025-04-02", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-04-02-ad-2025-nr-18/", False, False),
    ("AD 2025 nr 19", "2025-04-02", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-04-02-ad-2025-nr-19/", False, False),
    ("AD 2025 nr 20", "2025-04-02", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-04-02-ad-2025-nr-20/", False, False),
    ("AD 2025 nr 21", "2025-04-04", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-04-04-ad-2025-nr-21/", False, False),
    ("AD 2025 nr 22", "2025-04-09", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-04-09-ad-2025-nr-22/", False, False),
    ("AD 2025 nr 23", "2025-04-25", "Försäkringskassan - avskedande handläggare", "/sv/meddelade-domar/arkiverade-domar/2025/2025-04-25-ad-2025-nr-23/", True, False),
    ("AD 2025 nr 24", "2025-04-30", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-04-30-ad-2025-nr-24/", False, True),
    ("AD 2025 nr 25", "2025-04-30", "Projektledare - bisysslor brandman", "/sv/meddelade-domar/arkiverade-domar/2025/2025-04-30-ad-2025-nr-25/", True, False),
    ("AD 2025 nr 26", "2025-04-30", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-04-30-ad-2025-nr-26/", False, False),
    ("AD 2025 nr 27", "2025-04-30", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-04-30-ad-2025-nr-27/", False, False),
    ("AD 2025 nr 28", "2025-05-12", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-05-12-ad-2025-nr-28/", False, False),
    ("AD 2025 nr 29", "2025-05-14", "Taxichaufförer - anställning och övertidsersättning", "/sv/meddelade-domar/arkiverade-domar/2025/2025-05-14-ad-2025-nr-29/", True, False),
    ("AD 2025 nr 30", "2025-05-14", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-05-14-ad-2025-nr-30/", False, False),
    ("AD 2025 nr 31", "2025-05-20", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-05-20-ad-2025-nr-31/", False, False),
    ("AD 2025 nr 32", "2025-05-21", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-05-21-ad-2025-nr-32/", False, False),
    ("AD 2025 nr 33", "2025-05-21", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-05-21-ad-2025-nr-33/", False, False),
    ("AD 2025 nr 34", "2025-05-21", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-05-21-ad-2025-nr-34/", False, False),
    ("AD 2025 nr 35", "2025-05-26", "Stridsåtgärder - hamnarbetare", "/sv/meddelade-domar/arkiverade-domar/2025/2025-05-26-ad-2025-nr-35/", True, False),
    ("AD 2025 nr 36", "2025-05-28", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-05-28-ad-2025-nr-36/", False, False),
    ("AD 2025 nr 37", "2025-06-03", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-06-03-ad-2025-nr-37/", False, False),
    ("AD 2025 nr 38", "2025-06-11", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-06-11-ad-2025-nr-38/", False, True),
    ("AD 2025 nr 39", "2025-06-11", "Bemanningsavtal - timlön beräkning divisor", "/sv/meddelade-domar/arkiverade-domar/2025/2025-06-11-ad-2025-nr-39/", True, False),
    ("AD 2025 nr 40", "2025-06-09", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-06-09-ad-2025-nr-40/", False, False),
    ("AD 2025 nr 41", "2025-06-11", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-06-11-ad-2025-nr-41/", False, False),
    ("AD 2025 nr 42", "2025-06-12", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-06-12-ad-2025-nr-42/", False, False),
    ("AD 2025 nr 43", "2025-06-18", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-06-18-ad-2025-nr-43/", False, True),
    ("AD 2025 nr 44", "2025-06-18", "Arbetsmiljölagen - skyddsombud försäljning verksamhetsgren", "/sv/meddelade-domar/arkiverade-domar/2025/2025-06-18-ad-2025-nr-44/", True, False),
    ("AD 2025 nr 45", "2025-06-18", "Stridsåtgärder - hamnarbetare kollektivavtal", "/sv/meddelade-domar/arkiverade-domar/2025/2025-06-18-ad-2025-nr-45/", True, False),
    ("AD 2025 nr 46", "2025-06-25", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-06-25-ad-2025-nr-46/", False, True),
    ("AD 2025 nr 47", "2025-06-25", "Visselblåsarlagen - plastikkirurgi klinik", "/sv/meddelade-domar/arkiverade-domar/2025/2025-06-25-ad-2025-nr-47/", True, False),
    ("AD 2025 nr 48", "2025-06-24", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-06-24-ad-2025-nr-48/", False, False),
    ("AD 2025 nr 49", "2025-06-25", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-06-25-ad-2025-nr-49/", False, False),
    ("AD 2025 nr 50", "2025-07-02", "Uppsägning - bevisbörda förfalskad handlining", "/sv/meddelade-domar/arkiverade-domar/2025/2025-07-02-ad-2025-nr-50/", True, False),
    ("AD 2025 nr 51", "2025-07-08", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-07-08-ad-2025-nr-51/", False, False),
    ("AD 2025 nr 52", "2025-07-11", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-07-11-ad-2025-nr-52/", False, False),
    ("AD 2025 nr 53", "2025-07-23", "Biståndshandläggare - föräldraledighet missgynnande", "/sv/meddelade-domar/arkiverade-domar/2025/2025-07-23-ad-2025-nr-53/", True, False),
    ("AD 2025 nr 54", "2025-07-23", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-07-23-ad-2025-nr-54/", False, False),
    ("AD 2025 nr 55", "2025-08-06", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-08-06-ad-2025-nr-55/", False, False),
    ("AD 2025 nr 56", "2025-08-13", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-08-13-ad-2025-nr-56/", False, False),
    ("AD 2025 nr 57", "2025-08-20", "Gravida lärare - mödraskyddsdirektiv", "/sv/meddelade-domar/arkiverade-domar/2025/2025-08-20-ad-2025-nr-57/", True, False),
    ("AD 2025 nr 58", "2025-08-21", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-08-21-ad-2025-nr-58/", False, False),
    ("AD 2025 nr 59", "2025-08-22", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-08-22-ad-2025-nr-59/", False, False),
    ("AD 2025 nr 60", "2025-08-27", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-08-27-ad-2025-nr-60/", False, True),
    ("AD 2025 nr 61", "2025-09-03", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-09-03-ad-2025-nr-61/", False, False),
    ("AD 2025 nr 62", "2025-09-03", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-09-03-ad-2025-nr-62/", False, False),
    ("AD 2025 nr 63", "2025-09-04", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-09-04-ad-2025-nr-63/", False, False),
    ("AD 2025 nr 64", "2025-09-05", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-09-05-ad-2025-nr-64/", False, False),
    ("AD 2025 nr 65", "2025-09-10", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-09-10-ad-2025-nr-65/", False, False),
    ("AD 2025 nr 66", "2025-09-16", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-09-16-ad-2025-nr-66/", False, False),
    ("AD 2025 nr 67", "2025-09-17", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-09-17-ad-2025-nr-67/", False, False),
    ("AD 2025 nr 68", "2025-09-24", "Snöbollen ljuslykt - royalty arbetstvist", "/sv/meddelade-domar/arkiverade-domar/2025/2025-09-24-ad-2025-nr-68/", True, False),
    ("AD 2025 nr 69", "2025-09-24", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-09-24-ad-2025-nr-69/", False, False),
    ("AD 2025 nr 70", "2025-10-01", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-10-01-ad-2025-nr-70/", False, True),
    ("AD 2025 nr 71", "2025-10-01", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-10-01-ad-2025-nr-71/", False, False),
    ("AD 2025 nr 72", "2025-10-01", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-10-01-ad-2025-nr-72/", False, False),
    ("AD 2025 nr 73", "2025-10-01", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-10-01-ad-2025-nr-73/", False, False),
    ("AD 2025 nr 74", "2025-10-02", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-10-02-ad-2025-nr-74/", False, False),
    ("AD 2025 nr 75", "2025-10-03", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-10-03-ad-2025-nr-75/", False, False),
    ("AD 2025 nr 76", "2025-10-08", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-10-08-ad-2025-nr-76/", False, False),
    ("AD 2025 nr 77", "2025-10-08", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-10-08-ad-2025-nr-77/", False, False),
    ("AD 2025 nr 78", "2025-10-15", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-10-15-ad-2025-nr-78/", False, False),
    ("AD 2025 nr 79", "2025-10-16", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-10-16-ad-2025-nr-79/", False, False),
    ("AD 2025 nr 80", "2025-10-16", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-10-16-ad-2025-nr-80/", False, False),
    ("AD 2025 nr 81", "2025-10-16", "Facklig rättshjälp - rättegångskostnad", "/sv/meddelade-domar/arkiverade-domar/2025/2025-10-16-ad-2025-nr-81/", True, False),
    ("AD 2025 nr 82", "2025-10-22", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-10-22-ad-2025-nr-82/", False, True),
    ("AD 2025 nr 83", "2025-10-24", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-10-24-ad-2025-nr-83/", False, False),
    ("AD 2025 nr 84", "2025-10-24", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-10-24-ad-2025-nr-84/", False, False),
    ("AD 2025 nr 85", "2025-10-29", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-10-29-ad-2025-nr-85/", False, True),
    ("AD 2025 nr 86", "2025-11-03", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-11-03-ad-2025-nr-86/", False, False),
    ("AD 2025 nr 87", "2025-11-05", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-11-05-ad-2025-nr-87/", False, False),
    ("AD 2025 nr 88", "2025-11-12", "Dotterbolag - förhandlingsskyldighet aktieförsäljning", "/sv/meddelade-domar/arkiverade-domar/2025/2025-11-12-ad-2025-nr-88/", True, False),
    ("AD 2025 nr 89", "2025-11-12", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-11-12-ad-2025-nr-89/", False, False),
    ("AD 2025 nr 90", "2025-11-13", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-11-13-ad-2025-nr-90/", False, False),
    ("AD 2025 nr 91", "2025-11-13", "Ljudinspelning - allmän handling domstolsbeslut", "/sv/meddelade-domar/arkiverade-domar/2025/2025-11-13-ad-2025-nr-91/", True, False),
    ("AD 2025 nr 92", "2025-11-20", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-11-20-ad-2025-nr-92/", False, False),
    ("AD 2025 nr 93", "2025-11-24", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-11-24-ad-2025-nr-93/", False, False),
    ("AD 2025 nr 94", "2025-11-27", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-11-27-ad-2025-nr-94/", False, False),
    ("AD 2025 nr 95", "2025-12-02", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-12-02-ad-2025-nr-95/", False, False),
    ("AD 2025 nr 96", "2025-12-08", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-12-08-ad-2025-nr-96/", False, False),
    ("AD 2025 nr 97", "2025-12-17", "Uppsägning - preskription anställningsskyddslagen", "/sv/meddelade-domar/arkiverade-domar/2025/2025-12-17-ad-2025-nr-97/", True, False),
    ("AD 2025 nr 98", "2025-12-17", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-12-17-ad-2025-nr-98/", False, True),
    ("AD 2025 nr 99", "2025-12-17", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-12-17-ad-2025-nr-99/", False, True),
    ("AD 2025 nr 100", "2025-12-17", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-12-17-ad-2025-nr-100/", False, False),
    ("AD 2025 nr 101", "2025-12-18", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-12-18-ad-2005-nr-101/", False, False),
    ("AD 2025 nr 102", "2025-12-22", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-12-22-ad-2025-nr-102/", False, False),
    ("AD 2025 nr 103", "2025-12-23", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-12-23-ad-2025-nr-103/", False, False),
    ("AD 2025 nr 104", "2025-12-30", "Domen refereras inte", "/sv/meddelade-domar/arkiverade-domar/2025/2025-12-30-ad-2025-nr-104/", False, False),
]

conn = sqlite3.connect('arbetsdomstolen.db')
cursor = conn.cursor()

base_url = "https://arbetsdomstolen.se"

for malnummer, datum, titel, url, refererad, anonymiserad in domar:
    full_url = base_url + url
    cursor.execute('''
        INSERT OR REPLACE INTO domar (malnummer, datum, titel, url, refererad, anonymiserad)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (malnummer, datum, titel, full_url, refererad, anonymiserad))

conn.commit()
print(f"Lade till {len(domar)} domar i databasen.")

# Visa statistik
cursor.execute("SELECT COUNT(*) FROM domar")
total = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM domar WHERE refererad = 1")
refererade = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM domar WHERE anonymiserad = 1")
anonymiserade = cursor.fetchone()[0]

print(f"\nStatistik:")
print(f"  Totalt antal domar: {total}")
print(f"  Refererade domar: {refererade}")
print(f"  Anonymiserade domar: {anonymiserade}")

conn.close()
