# adfall

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](pyproject.toml)
[![MCP](https://img.shields.io/badge/MCP-server-111827.svg)](mcp_server.py)

Adfall är en read-only MCP-server och SQLite-databas för svenska
Arbetsdomstolen-domar, kompletterad med utvalda lagtexter och förarbeten från
`lagen.nu` och `riksdagen.se`.

Projektet är tänkt som en källdatabas för research, sökning och AI-assisterad
analys. Det är inte juridisk rådgivning och ersätter inte egen rättslig
bedömning.

## Snabbstart

Installera beroenden:

```bash
uv sync
```

Kör MCP-servern lokalt via stdio:

```bash
uv run python mcp_server.py
```

Använd en annan databasfil:

```bash
ADFALL_DB_PATH=/path/to/arbetsdomstolen.db uv run python mcp_server.py
```

Exempel på MCP-klientkonfiguration:

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

## Vad ingår?

| Del | Beskrivning |
| --- | --- |
| `mcp_server.py` | Read-only MCP-server med tools, resources och prompt. |
| `arbetsdomstolen.db.xz` | Komprimerad SQLite-databas som används vid deploy. |
| `arbetsdomstolen.db` | Lokal okomprimerad databas, git-ignorerad. |
| `pdfs/` | Lokalt arbetsmaterial för import och textutvinning, git-ignorerat. |
| Importskript | Skript för att bygga, komplettera och kontrollera datan. |
| `Dockerfile`, `railway.toml` | Deploykonfiguration för Railway. |

## Datainnehåll

Nuvarande lokala databas innehåller:

| Tabell | Innehåll | Antal |
| --- | --- | ---: |
| `domar` | AD-domar med metadata, sammanfattning, lagrum, rättsfrågor, domslut och fulltext där den finns | 2 594 |
| `laws` | Utvalda lagtexter kopplade till dommaterialet | 7 |
| `forarbeten` | Förarbetsdokument från lagen.nu och riksdagen.se | 150 |
| `law_forarbeten` | Kopplingar mellan lagar och förarbeten | - |

Domdatabasen täcker år 1993-2025.

## MCP-yta

### Tools

- `database_stats`
- `search_ad_cases`
- `get_ad_case`
- `find_cases_by_law`
- `search_law_text`
- `get_law`
- `get_forarbeten_for_law`
- `search_forarbeten`

### Resources

- `adfall://answer-guidance`
- `adfall://case/{malnummer}`
- `adfall://law/{sfs}`
- `adfall://forarbete/{doc_id}`

### Prompts

- `adfall_answer_guidance`

Servern skickar med svarsinstruktioner för juridiska svar som bygger på
AD-domar. När domar används som stöd ska svaret koppla domen till användarens
faktiska omständigheter och avslutas med:

```markdown
## Domar som bär slutsatsen

| Dom | Relevans i caset | Princip |
```

Domverktygen returnerar även ett `answer_table`-fält per dom med `dom`,
`relevans_i_caset` och `princip_underlag`, så klientens modell får stöd nära
källmaterialet.

## Railway-deploy

Servern kan köras live med Streamable HTTP på `/mcp`.

```bash
railway init
railway up
railway domain
```

Railway använder `Dockerfile` och `railway.toml`. Health check ligger på
`/health`.

Deployen behöver inte `pdfs/` eller den okomprimerade databasen. Docker-bygget
packar upp `arbetsdomstolen.db.xz` till `/app/arbetsdomstolen.db`.

Remote MCP-URL:

```text
https://DIN-RAILWAY-DOMAIN/mcp
```

Som standard startar servern även utan API-nyckel, vilket gör `/mcp` publik. För
privat endpoint, sätt `ADFALL_API_KEY` i Railway:

```bash
railway variable set ADFALL_API_KEY="$(openssl rand -hex 32)"
```

Skicka sedan nyckeln från klienten:

```text
Authorization: Bearer <ADFALL_API_KEY>
```

För lugnare Railway-loggar dämpas MCP-bibliotekets interna info-loggar till
`WARNING` som standard. Sätt `ADFALL_MCP_LOG_LEVEL=INFO` vid felsökning.

## Underhåll

Bygg om och komprimera databasen:

```bash
uv run python optimize_database.py
sqlite3 arbetsdomstolen.db "VACUUM;"
xz -kf -9 arbetsdomstolen.db
```

Importera äldre AD-domar från lagen.nu:

```bash
python3 import_lagennu_1993_2010.py
```

Kontrollera diff mot lagen.nu:

```bash
./check_lagennu_diff.py --start 1993 --end 2023
./check_lagennu_diff.py --show-lists
```

Importera lagar och förarbeten:

```bash
python3 import_laws_forarbeten.py
python3 backfill_forarbeten_from_riksdagen.py
```

Övriga import- och kompletteringsskript:

- `add_2011_2019.py`
- `add_2020_2024.py`
- `populate_db.py`
- `fetch_all_details.py`
- `extract_pdf_text.py`
- `fix_old_urls.py`
- `update_summaries.py`

## GitHub och artefakter

Repo:t spårar källkod, konfiguration, låsfil, licens och den komprimerade
databasen `arbetsdomstolen.db.xz`.

Följande är lokala eller genererade artefakter och ska inte commitas:

- `arbetsdomstolen.db`
- `pdfs/`
- Python-cache och virtuella miljöer
- miljöfiler och hemligheter

## Datakällor

- [Arbetsdomstolen](https://arbetsdomstolen.se/)
- [lagen.nu](https://lagen.nu/)
- [riksdagen.se](https://www.riksdagen.se/sv/dokument-och-lagar)

## Kända avvikelser

- `AD 2013 nr 1` saknar PDF-länk på källsidan.
- `AD 2019 nr 53` har PDF men fulltext kunde inte extraheras automatiskt.

## Licens

Open source under [MIT License](LICENSE).
