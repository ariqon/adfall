#!/usr/bin/env python3
"""MCP server for the local Arbetsdomstolen database.

The server exposes narrow, read-only tools over ``arbetsdomstolen.db``.  The
query helpers are intentionally plain sqlite3 so they can be tested without an
MCP runtime installed; running the server itself requires the official
``mcp[cli]`` Python package.
"""

from __future__ import annotations

import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Awaitable, Callable
from urllib.parse import quote, unquote

try:
    from mcp.server.fastmcp import FastMCP
    from mcp.server.transport_security import TransportSecuritySettings
except ImportError:  # pragma: no cover - exercised only when dependency is missing
    FastMCP = None  # type: ignore[assignment]
    TransportSecuritySettings = None  # type: ignore[assignment]

try:
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    from starlette.types import ASGIApp, Receive, Scope, Send
except ImportError:  # pragma: no cover - provided by the MCP runtime dependency
    Starlette = None  # type: ignore[assignment]
    Request = None  # type: ignore[assignment]
    JSONResponse = None  # type: ignore[assignment]
    Route = None  # type: ignore[assignment]
    ASGIApp = Any  # type: ignore[misc,assignment]
    Receive = Any  # type: ignore[misc,assignment]
    Scope = Any  # type: ignore[misc,assignment]
    Send = Any  # type: ignore[misc,assignment]


ROOT = Path(__file__).resolve().parent
DEFAULT_DB_PATH = ROOT / "arbetsdomstolen.db"
SERVER_NAME = "adfall"
MAX_LIMIT = 50
DEFAULT_TEXT_CHARS = 6000
DEFAULT_HTTP_PATH = "/mcp"


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


def _mcp_path() -> str:
    path = os.environ.get("ADFALL_MCP_PATH", DEFAULT_HTTP_PATH).strip() or DEFAULT_HTTP_PATH
    return path if path.startswith("/") else f"/{path}"


def _csv_env(name: str, default: list[str]) -> list[str]:
    value = os.environ.get(name)
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


mcp = (
    FastMCP(
        SERVER_NAME,
        host=os.environ.get("HOST", "127.0.0.1"),
        port=_env_int("PORT", 8000),
        streamable_http_path=_mcp_path(),
        stateless_http=os.environ.get("ADFALL_STATELESS_HTTP", "true").lower()
        not in {"0", "false", "no"},
        transport_security=TransportSecuritySettings(
            allowed_hosts=_csv_env(
                "ADFALL_ALLOWED_HOSTS",
                [
                    "127.0.0.1",
                    "localhost",
                    "adfall-mcp-production.up.railway.app",
                ],
            ),
            allowed_origins=_csv_env(
                "ADFALL_ALLOWED_ORIGINS",
                [
                    "https://adfall-mcp-production.up.railway.app",
                ],
            ),
        ),
    )
    if FastMCP and TransportSecuritySettings
    else None
)


def _register_tool(func):
    return mcp.tool()(func) if mcp else func


def _register_resource(uri: str):
    def decorator(func):
        return mcp.resource(uri)(func) if mcp else func

    return decorator


def _db_path() -> Path:
    return Path(os.environ.get("ADFALL_DB_PATH", DEFAULT_DB_PATH)).expanduser().resolve()


def _connect() -> sqlite3.Connection:
    path = _db_path()
    if not path.exists():
        raise FileNotFoundError(f"Database not found: {path}")

    uri = f"file:{quote(path.as_posix(), safe='/:')}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _api_key() -> str | None:
    return os.environ.get("ADFALL_API_KEY")


class ApiKeyMiddleware:
    """Small Bearer/X-API-Key guard for private remote deployments."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope.get("path") == "/health":
            await self.app(scope, receive, send)
            return

        expected = _api_key()
        if not expected:
            await self.app(scope, receive, send)
            return

        headers = {
            key.decode("latin1").lower(): value.decode("latin1")
            for key, value in scope.get("headers", [])
        }
        authorization = headers.get("authorization", "")
        bearer = authorization.removeprefix("Bearer ").strip()
        provided = bearer or headers.get("x-api-key", "")

        if provided != expected:
            response = JSONResponse({"error": "Unauthorized"}, status_code=401)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


async def health(_request: Request) -> JSONResponse:
    return JSONResponse({"ok": True, "server": SERVER_NAME})


def create_app() -> Starlette:
    if mcp is None or Starlette is None:
        raise RuntimeError("Missing MCP/Starlette dependencies. Install `mcp[cli]`.")

    app = mcp.streamable_http_app()
    app.add_route("/health", health, methods=["GET"])
    return ApiKeyMiddleware(app)


app = create_app() if mcp and Starlette else None


def _rows(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with _connect() as conn:
        return [dict(row) for row in conn.execute(sql, params).fetchall()]


def _row(sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    with _connect() as conn:
        result = conn.execute(sql, params).fetchone()
        return dict(result) if result else None


def _scalar(sql: str, params: tuple[Any, ...] = ()) -> Any:
    with _connect() as conn:
        return conn.execute(sql, params).fetchone()[0]


def _limit(limit: int | None) -> int:
    if limit is None:
        return 10
    return max(1, min(int(limit), MAX_LIMIT))


def _clip(text: str | None, chars: int | None = DEFAULT_TEXT_CHARS) -> str | None:
    if text is None:
        return None
    max_chars = max(500, min(int(chars or DEFAULT_TEXT_CHARS), 50000))
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n\n[...truncated...]"


def _like(query: str) -> str:
    escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _table_exists(name: str) -> bool:
    return bool(
        _row(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type IN ('table', 'virtual table') AND name = ?
            """,
            (name,),
        )
    )


def _fts_query(query: str) -> str:
    tokens = re.findall(r"[\wÅÄÖåäö]+", query, flags=re.UNICODE)
    return " ".join(f'"{token}"*' if len(token) >= 3 else f'"{token}"' for token in tokens)


def _snippet(text: str | None, query: str | None, chars: int = 600) -> str | None:
    if not text:
        return None

    clean = re.sub(r"\s+", " ", text).strip()
    if not clean:
        return None

    if query:
        match = re.search(re.escape(query), clean, flags=re.IGNORECASE)
        if match:
            start = max(0, match.start() - chars // 3)
            end = min(len(clean), start + chars)
            prefix = "..." if start else ""
            suffix = "..." if end < len(clean) else ""
            return prefix + clean[start:end].strip() + suffix

    return _clip(clean, chars)


def _case_summary(row: dict[str, Any], query: str | None = None) -> dict[str, Any]:
    return {
        "malnummer": row["malnummer"],
        "datum": row["datum"],
        "titel": row.get("titel"),
        "refererad": bool(row.get("refererad")),
        "anonymiserad": bool(row.get("anonymiserad")),
        "lagrum": row.get("lagrum"),
        "rattsfragor": row.get("rattsfragor"),
        "url": row.get("url"),
        "pdf_path": row.get("pdf_path"),
        "has_fulltext": bool(row.get("fulltext")),
        "snippet": _snippet(
            row.get("fulltext")
            or row.get("sammanfattning")
            or row.get("rattsfragor")
            or row.get("lagrum")
            or row.get("titel"),
            query,
        ),
    }


def _case_by_malnummer(malnummer: str) -> dict[str, Any] | None:
    return _row(
        """
        SELECT *
        FROM domar
        WHERE malnummer = ? COLLATE NOCASE
        """,
        (malnummer.strip(),),
    )


@_register_tool
def database_stats() -> dict[str, Any]:
    """Return high-level counts and date coverage for the AD database."""

    stats = _row(
        """
        SELECT
            COUNT(*) AS total_cases,
            MIN(datum) AS first_case_date,
            MAX(datum) AS latest_case_date,
            SUM(CASE WHEN fulltext IS NOT NULL AND fulltext != '' THEN 1 ELSE 0 END) AS cases_with_fulltext,
            SUM(CASE WHEN refererad = 1 THEN 1 ELSE 0 END) AS referenced_cases,
            SUM(CASE WHEN anonymiserad = 1 THEN 1 ELSE 0 END) AS anonymized_cases
        FROM domar
        """
    )
    return {
        **(stats or {}),
        "laws": _scalar("SELECT COUNT(*) FROM laws"),
        "forarbeten": _scalar("SELECT COUNT(*) FROM forarbeten"),
        "database_path": str(_db_path()),
    }


@_register_tool
def search_ad_cases(
    query: str = "",
    year_from: int | None = None,
    year_to: int | None = None,
    refererad: bool | None = None,
    anonymiserad: bool | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search AD cases by text, year range, and case flags."""

    clauses: list[str] = []
    params: list[Any] = []
    query_text = query.strip()

    if query_text and _table_exists("domar_fts"):
        fts_query = _fts_query(query_text)
        if fts_query:
            clauses.append("domar_fts MATCH ?")
            params.append(fts_query)

            if year_from is not None:
                clauses.append("CAST(strftime('%Y', d.datum) AS INTEGER) >= ?")
                params.append(int(year_from))
            if year_to is not None:
                clauses.append("CAST(strftime('%Y', d.datum) AS INTEGER) <= ?")
                params.append(int(year_to))
            if refererad is not None:
                clauses.append("d.refererad = ?")
                params.append(1 if refererad else 0)
            if anonymiserad is not None:
                clauses.append("d.anonymiserad = ?")
                params.append(1 if anonymiserad else 0)

            sql = f"""
                SELECT d.*
                FROM domar_fts
                JOIN domar d ON d.id = domar_fts.rowid
                WHERE {' AND '.join(clauses)}
                ORDER BY bm25(domar_fts), d.datum DESC, d.malnummer DESC
                LIMIT ?
            """
            params.append(_limit(limit))
            return [_case_summary(row, query_text) for row in _rows(sql, tuple(params))]

    if query_text:
        pattern = _like(query_text)
        searchable = [
            "malnummer",
            "titel",
            "sammanfattning",
            "parter",
            "lagrum",
            "rattsfragor",
            "domslut",
            "fulltext",
        ]
        clauses.append(
            "("
            + " OR ".join(
                f"COALESCE({column}, '') LIKE ? ESCAPE '\\'" for column in searchable
            )
            + ")"
        )
        params.extend([pattern] * len(searchable))

    if year_from is not None:
        clauses.append("CAST(strftime('%Y', datum) AS INTEGER) >= ?")
        params.append(int(year_from))
    if year_to is not None:
        clauses.append("CAST(strftime('%Y', datum) AS INTEGER) <= ?")
        params.append(int(year_to))
    if refererad is not None:
        clauses.append("refererad = ?")
        params.append(1 if refererad else 0)
    if anonymiserad is not None:
        clauses.append("anonymiserad = ?")
        params.append(1 if anonymiserad else 0)

    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    sql = f"""
        SELECT *
        FROM domar
        {where}
        ORDER BY datum DESC, malnummer DESC
        LIMIT ?
    """
    params.append(_limit(limit))
    return [_case_summary(row, query_text or None) for row in _rows(sql, tuple(params))]


@_register_tool
def get_ad_case(
    malnummer: str,
    include_fulltext: bool = False,
    fulltext_chars: int = DEFAULT_TEXT_CHARS,
) -> dict[str, Any]:
    """Fetch one AD case by citation, for example "AD 2025 nr 53"."""

    row = _case_by_malnummer(malnummer)
    if row is None:
        return {"error": f"No case found for {malnummer!r}"}

    result = {
        key: value
        for key, value in row.items()
        if key not in {"fulltext", "refererad", "anonymiserad"}
    }
    result["refererad"] = bool(row.get("refererad"))
    result["anonymiserad"] = bool(row.get("anonymiserad"))
    result["has_fulltext"] = bool(row.get("fulltext"))
    if include_fulltext:
        result["fulltext"] = _clip(row.get("fulltext"), fulltext_chars)
    return result


@_register_tool
def find_cases_by_law(law_reference: str, limit: int = 10) -> list[dict[str, Any]]:
    """Find AD cases whose lagrum mentions an SFS number or law name."""

    pattern = _like(law_reference.strip())
    rows = _rows(
        """
        SELECT *
        FROM domar
        WHERE COALESCE(lagrum, '') LIKE ? ESCAPE '\\'
        ORDER BY datum DESC, malnummer DESC
        LIMIT ?
        """,
        (pattern, _limit(limit)),
    )
    return [_case_summary(row, law_reference.strip()) for row in rows]


@_register_tool
def search_law_text(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search imported law titles and fulltexts."""

    query_text = query.strip()
    if query_text and _table_exists("laws_fts"):
        fts_query = _fts_query(query_text)
        if fts_query:
            rows = _rows(
                """
                SELECT l.sfs, l.title, l.url, l.source_name, l.source_ref, l.fulltext
                FROM laws_fts
                JOIN laws l ON l.rowid = laws_fts.rowid
                WHERE laws_fts MATCH ?
                ORDER BY bm25(laws_fts), l.sfs
                LIMIT ?
                """,
                (fts_query, _limit(limit)),
            )
            return [
                {
                    "sfs": row["sfs"],
                    "title": row["title"],
                    "url": row["url"],
                    "source_name": row["source_name"],
                    "source_ref": row["source_ref"],
                    "snippet": _snippet(row.get("fulltext") or row.get("title"), query_text),
                }
                for row in rows
            ]

    pattern = _like(query.strip())
    rows = _rows(
        """
        SELECT sfs, title, url, source_name, source_ref, fulltext
        FROM laws
        WHERE title LIKE ? ESCAPE '\\' OR COALESCE(fulltext, '') LIKE ? ESCAPE '\\'
        ORDER BY sfs
        LIMIT ?
        """,
        (pattern, pattern, _limit(limit)),
    )
    return [
        {
            "sfs": row["sfs"],
            "title": row["title"],
            "url": row["url"],
            "source_name": row["source_name"],
            "source_ref": row["source_ref"],
            "snippet": _snippet(row.get("fulltext") or row.get("title"), query.strip()),
        }
        for row in rows
    ]


@_register_tool
def get_law(
    sfs: str,
    include_fulltext: bool = True,
    fulltext_chars: int = DEFAULT_TEXT_CHARS,
) -> dict[str, Any]:
    """Fetch one imported law by SFS number, for example "1982:80"."""

    row = _row(
        """
        SELECT *
        FROM laws
        WHERE sfs = ?
        """,
        (sfs.strip(),),
    )
    if row is None:
        return {"error": f"No law found for {sfs!r}"}

    result = {key: value for key, value in row.items() if key != "fulltext"}
    result["has_fulltext"] = bool(row.get("fulltext"))
    if include_fulltext:
        result["fulltext"] = _clip(row.get("fulltext"), fulltext_chars)
    return result


@_register_tool
def get_forarbeten_for_law(
    sfs: str,
    include_fulltext: bool = False,
    fulltext_chars: int = DEFAULT_TEXT_CHARS,
    limit: int = MAX_LIMIT,
) -> list[dict[str, Any]]:
    """List preparatory works linked to a specific SFS number."""

    rows = _rows(
        """
        SELECT f.*, lf.ref_label, lf.ref_url
        FROM law_forarbeten lf
        JOIN forarbeten f ON f.doc_id = lf.doc_id
        WHERE lf.sfs = ?
        ORDER BY f.doc_id
        LIMIT ?
        """,
        (sfs.strip(), _limit(limit)),
    )
    results = []
    for row in rows:
        item = {key: value for key, value in row.items() if key != "fulltext"}
        item["has_fulltext"] = bool(row.get("fulltext"))
        if include_fulltext:
            item["fulltext"] = _clip(row.get("fulltext"), fulltext_chars)
        else:
            item["snippet"] = _snippet(row.get("fulltext"), row.get("title"))
        results.append(item)
    return results


@_register_tool
def search_forarbeten(
    query: str,
    doc_type: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search imported preparatory works by title and fulltext."""

    query_text = query.strip()
    if query_text and _table_exists("forarbeten_fts"):
        fts_query = _fts_query(query_text)
        if fts_query:
            clauses = ["forarbeten_fts MATCH ?"]
            params: list[Any] = [fts_query]

            if doc_type:
                clauses.append("f.doc_type = ?")
                params.append(doc_type.strip())

            sql = f"""
                SELECT f.*
                FROM forarbeten_fts
                JOIN forarbeten f ON f.rowid = forarbeten_fts.rowid
                WHERE {' AND '.join(clauses)}
                ORDER BY bm25(forarbeten_fts), f.doc_id
                LIMIT ?
            """
            params.append(_limit(limit))
            rows = _rows(sql, tuple(params))
            return [
                {
                    "doc_id": row["doc_id"],
                    "doc_type": row["doc_type"],
                    "title": row["title"],
                    "url": row["url"],
                    "source_name": row["source_name"],
                    "source_ref": row["source_ref"],
                    "has_fulltext": bool(row.get("fulltext")),
                    "snippet": _snippet(row.get("fulltext") or row.get("title"), query_text),
                }
                for row in rows
            ]

    clauses = [
        "(title LIKE ? ESCAPE '\\' OR COALESCE(fulltext, '') LIKE ? ESCAPE '\\')"
    ]
    params: list[Any] = [_like(query.strip()), _like(query.strip())]

    if doc_type:
        clauses.append("doc_type = ?")
        params.append(doc_type.strip())

    sql = f"""
        SELECT *
        FROM forarbeten
        WHERE {' AND '.join(clauses)}
        ORDER BY doc_id
        LIMIT ?
    """
    params.append(_limit(limit))
    rows = _rows(sql, tuple(params))
    return [
        {
            "doc_id": row["doc_id"],
            "doc_type": row["doc_type"],
            "title": row["title"],
            "url": row["url"],
            "source_name": row["source_name"],
            "source_ref": row["source_ref"],
            "has_fulltext": bool(row.get("fulltext")),
            "snippet": _snippet(row.get("fulltext") or row.get("title"), query.strip()),
        }
        for row in rows
    ]


@_register_resource("adfall://case/{malnummer}")
def case_resource(malnummer: str) -> dict[str, Any]:
    """Resource view of one AD case."""

    return get_ad_case(unquote(malnummer), include_fulltext=True)


@_register_resource("adfall://law/{sfs}")
def law_resource(sfs: str) -> dict[str, Any]:
    """Resource view of one imported law."""

    return get_law(unquote(sfs), include_fulltext=True)


@_register_resource("adfall://forarbete/{doc_id}")
def forarbete_resource(doc_id: str) -> dict[str, Any]:
    """Resource view of one preparatory-work document."""

    doc_id = unquote(doc_id)
    row = _row("SELECT * FROM forarbeten WHERE doc_id = ?", (doc_id.strip(),))
    if row is None:
        return {"error": f"No forarbete found for {doc_id!r}"}
    result = {key: value for key, value in row.items() if key != "fulltext"}
    result["fulltext"] = _clip(row.get("fulltext"), DEFAULT_TEXT_CHARS)
    result["has_fulltext"] = bool(row.get("fulltext"))
    return result


def main() -> None:
    if mcp is None:
        raise SystemExit(
            "Missing dependency: install with `uv add \"mcp[cli]\"` "
            "or `python3 -m pip install \"mcp[cli]\"`."
        )

    transport = os.environ.get("ADFALL_TRANSPORT", "stdio")
    if transport == "streamable-http":
        import uvicorn

        if not _api_key():
            print(
                "WARNING: ADFALL_API_KEY is not set; remote MCP endpoint is public.",
                file=sys.stderr,
            )
        uvicorn.run(
            "mcp_server:app",
            host=os.environ.get("HOST", "0.0.0.0"),
            port=_env_int("PORT", 8000),
            log_level=os.environ.get("LOG_LEVEL", "info").lower(),
        )
        return

    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
