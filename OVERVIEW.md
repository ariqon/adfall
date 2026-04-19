# Översikt: vad som har gjorts

## Mål

Bygga en lokal databas med AD-domar och komplettera med centrala lagar samt relevanta förarbeten, begränsat till specificerade SFS.

## Genomfört arbete

1. Inventerat projektet och verifierat dataläge i `arbetsdomstolen.db`.
2. Kontrollerat täckning för AD-domar och identifierat datakvalitetsluckor.
3. Importerat AD 1993-2010 från `lagen.nu`:
- Script: `import_lagennu_1993_2010.py`
- Lagt in källmärkning i `domar` via `source_name` och `source_ref`.
4. Byggt diff-verktyg mot `lagen.nu`:
- Script: `check_lagennu_diff.py`
- Verifierat att AD 1993-2023 har `missing=0` mot lagen.nu (med 20 lokala extra för 2023 nr 58-77).
5. Importerat lagar och förarbeten för utvalda lagar:
- Script: `import_laws_forarbeten.py`
- Tabeller: `laws`, `forarbeten`, `law_forarbeten`.
6. Kompletterat saknade förarbeten via Riksdagens öppna data:
- Script: `backfill_forarbeten_from_riksdagen.py`
- Fyllde 22 tidigare otillgängliga poster från `riksdagen.se`.

## Omfattning

### AD-domar
- Intervall i DB: 1993-2025
- Totalt i `domar`: 2594

### Lagar (SFS)
- 1976:580
- 1982:80
- 1974:371
- 1977:480
- 1982:673
- 1994:260
- 2021:890

### Förarbeten
- Totalt: 150 relevanta förarbetsdokument kopplade till lagarna ovan.
- Källor:
- `lagen.nu`: 128
- `riksdagen.se`: 22

## Kvarvarande kända punkter

- `AD 2013 nr 1`: saknar hittad PDF-länk från källsidan.
- `AD 2019 nr 53`: PDF finns, men fulltext-extraktion har misslyckats och kräver alternativ metod (t.ex. OCR).
