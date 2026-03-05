FROM python:3.13-slim AS deps

COPY --from=ghcr.io/astral-sh/uv:0.9.2 /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-dev --extra api --no-install-project


FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=deps /app/.venv /app/.venv
COPY services/api/src /app/src

RUN groupadd --system app && useradd --system --gid app --home-dir /app app && chown -R app:app /app

USER app

CMD ["uvicorn", "api_app.main:app", "--host", "0.0.0.0", "--port", "8080"]
