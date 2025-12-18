FROM python:3.13-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl libcurl4-openssl-dev libssl-dev \
  && rm -rf /var/lib/apt/lists/*

COPY Pipfile Pipfile.lock* ./
RUN pip install --no-cache-dir pipenv \
  && pipenv requirements --dev > requirements.txt \
  && pip install --no-cache-dir -r requirements.txt --prefix=/install

FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl libcurl4 \
  && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local
COPY . .

# Prove Django is installed, then collectstatic with verbose logs
RUN DJANGO_ENV=ci \
    python manage.py collectstatic --noinput --verbosity 2

EXPOSE 8000
CMD ["gunicorn", "mahjong_api.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--log-level", "info", "--timeout", "60"]
