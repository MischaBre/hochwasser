FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

COPY services/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY services/api/src /app/src

RUN groupadd --system app && useradd --system --gid app --home-dir /app app && chown -R app:app /app

USER app

CMD ["uvicorn", "api_app.main:app", "--host", "0.0.0.0", "--port", "8080"]
