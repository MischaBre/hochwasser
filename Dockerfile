FROM python:3.13-slim AS deps

COPY --from=ghcr.io/astral-sh/uv:0.9.2 /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-dev --extra alert --no-install-project


FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    MPLCONFIGDIR=/tmp/matplotlib \
    XDG_CACHE_HOME=/tmp/.cache

WORKDIR /app

COPY --from=deps /app/.venv /app/.venv
COPY app /app/app
COPY templates /app/templates
COPY locales /app/locales

RUN groupadd --system app && useradd --system --gid app --home-dir /app app && chown -R app:app /app

USER app

CMD ["python", "-m", "app.main"]
