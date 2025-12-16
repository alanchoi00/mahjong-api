FROM python:3.13-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl \
  && rm -rf /var/lib/apt/lists/*

COPY Pipfile Pipfile.lock* ./
RUN pip install --no-cache-dir pipenv \
  && pipenv requirements > requirements.txt \
  && pip install --no-cache-dir -r requirements.txt --prefix=/install

# ---------- runtime ----------
FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl \
  && rm -rf /var/lib/apt/lists/*

# bring deps in
COPY --from=builder /install /usr/local

# bring code in
COPY . .

RUN DJANGO_SETTINGS_MODULE=mahjong_api.settings.ci \
    python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "mahjong_api.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--log-level", "info", "--timeout", "60"]
