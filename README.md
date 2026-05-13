# adfall

Datainsamling av Arbetsdomstolens domar till SQLite, med komplettering från `lagen.nu` och `riksdagen.se`.

## Innehåll

- Databas: `arbetsdomstolen.db`
- Domtabell: `domar`
- PDF:er: `pdfs/`
- Import/underhållsskript:
`add_2011_2019.py`, `add_2020_2024.py`, `populate_db.py`, `fetch_all_details.py`, `extract_pdf_text.py`, `fix_old_urls.py`, `update_summaries.py`, `import_lagennu_1993_2010.py`, `check_lagennu_diff.py`, `import_laws_forarbeten.py`, `backfill_forarbeten_from_riksdagen.py`

## Datakällor

- [arbetsdomstolen.se](https://arbetsdomstolen.se/)
- [lagen.nu](https://lagen.nu/)
- [riksdagen.se](https://www.riksdagen.se/sv/dokument-och-lagar)

## Tabeller

### `domar`
Innehåller AD-domar (målnummer, datum, titel, URL, sammanfattning, lagrum, rättsfrågor, domslut, PDF/fulltext, källmärkning).

### `laws`
Utvalda lagar (SFS), lagtitel, URL och fulltext.

### `forarbeten`
Förarbetsdokument (doc_id, typ, titel, URL, fulltext, källa).

### `law_forarbeten`
Kopplingstabell mellan lag (`sfs`) och förarbete (`doc_id`).

## Körning

### MCP-server

Projektet innehåller en read-only MCP-server i `mcp_server.py` som exponerar databasen som tools och resources.

Installera beroenden:

```bash
uv sync
```

Kör servern lokalt via stdio:

```bash
uv run python mcp_server.py
```

Om databasen ligger någon annanstans:

```bash
ADFALL_DB_PATH=/path/to/arbetsdomstolen.db uv run python mcp_server.py
```

Exempel på klientkonfiguration:

```json
{
  "mcpServers": {
    "adfall": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/jsundlo/Projects/adfall",
        "run",
        "python",
        "mcp_server.py"
      ]
    }
  }
}
```

Exponerade tools:

- `database_stats`
- `search_ad_cases`
- `get_ad_case`
- `find_cases_by_law`
- `search_law_text`
- `get_law`
- `get_forarbeten_for_law`
- `search_forarbeten`

Exponerade resources:

- `adfall://case/{malnummer}`
- `adfall://law/{sfs}`
- `adfall://forarbete/{doc_id}`

### Railway-deploy

Servern kan även köras live med Streamable HTTP på `/mcp`.

```bash
railway init
railway up
railway domain
```

Railway använder `Dockerfile` och `railway.toml`. Health check ligger på `/health`.
Den okomprimerade databasen `arbetsdomstolen.db` är git-ignorerad, men Railway-bygget använder `arbetsdomstolen.db.xz` och packar upp den till `/app/arbetsdomstolen.db` i Docker-bygget.

Om databasen byggs om lokalt:

```bash
uv run python optimize_database.py
sqlite3 arbetsdomstolen.db "VACUUM;"
xz -kf -9 arbetsdomstolen.db
railway up
```

Remote MCP-URL:

```text
https://DIN-RAILWAY-DOMAIN/mcp
```

Som standard är endpointen publik. För privat endpoint, sätt `ADFALL_API_KEY` i Railway:

```bash
railway variable set ADFALL_API_KEY="$(openssl rand -hex 32)"
```

Skicka då nyckeln från klienten som:

```text
Authorization: Bearer <ADFALL_API_KEY>
```

Utan `ADFALL_API_KEY` startar servern ändå, men `/mcp` blir publik.

### 1) Import AD 1993-2010 från lagen.nu
```bash
python3 import_lagennu_1993_2010.py
```

### 2) Diff-kontroll mot lagen.nu
```bash
./check_lagennu_diff.py --start 1993 --end 2023
```

Med detaljer:
```bash
./check_lagennu_diff.py --show-lists
```

### 3) Import lagar + förarbeten för utvalt lagrum
```bash
python3 import_laws_forarbeten.py
```

### 4) Backfill av saknade förarbeten från riksdagen.se
```bash
python3 backfill_forarbeten_from_riksdagen.py
```

## Nuvarande status (kort)

- `domar`: 2594 poster
- AD 1993-2023: 0 saknade mot lagen.nu, 20 extra lokalt (2023 nr 58-77)
- Lagar inlästa: 7 unika SFS
- Relevanta förarbeten till dessa lagar: 150 (128 från lagen.nu + 22 från riksdagen.se)

## Kända avvikelser

- `AD 2013 nr 1` saknar PDF-länk på källsidan.
- `AD 2019 nr 53` har PDF men fulltext kunde inte extraheras automatiskt.
