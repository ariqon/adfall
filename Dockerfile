FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    ADFALL_TRANSPORT=streamable-http \
    ADFALL_DB_PATH=/app/arbetsdomstolen.db

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .
RUN python -c "import lzma, shutil; shutil.copyfileobj(lzma.open('arbetsdomstolen.db.xz', 'rb'), open('arbetsdomstolen.db', 'wb'))" \
    && rm arbetsdomstolen.db.xz

EXPOSE 8000

CMD ["uv", "run", "python", "mcp_server.py"]
