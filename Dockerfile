FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLCONFIGDIR=/tmp/matplotlib \
    XDG_CACHE_HOME=/tmp/.cache

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app /app/app
COPY templates /app/templates
COPY locales /app/locales

RUN groupadd --system app && useradd --system --gid app --home-dir /app app && chown -R app:app /app

USER app

CMD ["python", "-m", "app.main"]
