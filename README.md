# Mahjong API

A Django REST Framework backend for mahjong tile detection. Upload images of mahjong hands and get back detected tiles using YOLO-based machine learning inference.

## What is Mahjong?

Mahjong is a tile-based game that originated in China. Players draw and discard tiles to form winning combinations. This API helps players by automatically detecting tiles from photos of their hand, enabling features like:

- **Hand analysis**: Identify all tiles in a player's hand
- **Scoring assistance**: Calculate potential winning hands and points
- **Learning aid**: Help new players understand tile recognition

## Features

- **Presigned S3 Uploads**: Secure, direct-to-S3 file uploads via presigned URLs
- **ML Tile Detection**: YOLO-based object detection for identifying mahjong tiles from photos
- **Async Processing**: Celery task queue with AWS SQS for background inference jobs
- **Anonymous Clients**: Track app installations without requiring user accounts
- **S3 Model Loading**: Automatically downloads ML model weights from S3 at worker startup

## Architecture

```mermaid
flowchart TB
    subgraph Client
        Mobile[Mobile Client]
    end

    subgraph AWS
        S3[(S3 Bucket)]
        SQS[SQS Queue]
        S3Models[(S3 Models)]
    end

    subgraph Backend
        API[Django API]
        Worker[Celery Worker]
        DB[(PostgreSQL)]
        Model[YOLO Model]
    end

    Mobile -->|1. Request presigned URL| API
    API -->|2. Return presigned URL| Mobile
    Mobile -->|3. Upload image| S3
    Mobile -->|4. Complete upload| API
    API -->|5. Queue detection task| SQS
    API <--> DB
    SQS --> Worker
    S3Models -->|Download on startup| Worker
    Worker --> Model
    Worker --> S3
    Worker --> DB
```

### Django Apps

| App      | Description                                               |
| -------- | --------------------------------------------------------- |
| `core`   | Base models, custom DRF exception handling                |
| `user`   | Anonymous client tracking via `install_id`                |
| `asset`  | S3 upload sessions, asset storage, polymorphic references |
| `hand`   | Mahjong hand detection, Celery tasks                      |
| `rule`   | Mahjong rule sets (placeholder)                           |
| `ml`     | Machine learning inference and model loading              |

## Requirements

- Python 3.13+
- PostgreSQL 16+
- Docker (for running tests)
- AWS Account (S3, SQS)

## Quick Start

### 1. Clone and Install Dependencies

```bash
git clone <repository-url>
cd mahjong-api

# Install pipenv if needed
pip install pipenv

# Install dependencies
pipenv install --dev
```

### 2. Set Up PostgreSQL

```bash
# Using Docker
docker run -d \
  --name mahjong-postgres \
  -e POSTGRES_USER=mahjong \
  -e POSTGRES_PASSWORD=mahjong \
  -e POSTGRES_DB=mahjong \
  -p 5432:5432 \
  postgres:16-alpine
```

### 3. Configure Environment

Create a `.env` file in the project root:

```bash
# Database
DATABASE_URL=postgresql://mahjong:mahjong@localhost:5432/mahjong

# Django
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=*

# AWS Credentials
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_REGION=ap-southeast-2

# Celery (optional for local dev)
CELERY_BROKER_URL=sqs://
CELERY_SQS_QUEUE_URL=https://sqs.ap-southeast-2.amazonaws.com/xxx/queue-name

# ML Model (optional - has defaults)
MODEL_S3_URI=s3://your-bucket/ml/models/tile_detector/v0.1.0/model.pt
TILE_DETECTOR_MODEL_NAME=tile_detector
TILE_DETECTOR_MODEL_VERSION=v0.1.0
MODEL_DIR=/ml/models
```

### 4. Run Migrations

```bash
pipenv run migrate
```

### 5. Start Development Server

```bash
pipenv run start
```

The API will be available at `http://localhost:8000`.

## Development Commands

```bash
# Package management
pipenv install --dev          # Install all dependencies
pipenv shell                  # Activate virtualenv

# Development
pipenv run start              # Run dev server
pipenv run shell              # Django shell
pipenv run migrate            # Run migrations
pipenv run makemigrations     # Create migrations

# Testing
pipenv run test               # Run all tests
pipenv run python manage.py test <app>.tests.<TestClass>.<test_method>

# Linting
pipenv run ruff check .       # Check for issues
pipenv run ruff check . --fix # Auto-fix issues
```

## Testing

Tests use [testcontainers](https://testcontainers.com/) to spin up a PostgreSQL container automatically. Docker must be running.

```bash
# Run all tests
pipenv run test

# Run specific app tests
pipenv run python manage.py test asset

# Run specific test class
pipenv run python manage.py test asset.services.tests.test_uploads.TestCreatePresignedUpload
```

Test settings are auto-detected when running `manage.py test` - no environment variables needed.

## Project Structure

```
mahjong-api/
├── asset/                 # Upload & asset management
│   ├── models/            # Asset, UploadSession, AssetRef
│   ├── services/          # Business logic
│   │   ├── s3.py          # S3 operations (upload, download)
│   │   └── uploads.py     # Upload flow
│   ├── views/             # API endpoints
│   └── serializers/       # Request/response schemas
├── core/                  # Shared utilities
│   ├── models.py          # TimeStampedModel base
│   └── exceptions.py      # Custom API exceptions
├── hand/                  # Hand detection
│   ├── models/            # Hand model
│   └── tasks.py           # Celery tasks
├── ml/                    # Machine learning
│   ├── inference/
│   │   ├── model.py       # YOLO model loading
│   │   └── model_loader.py # S3 model download
│   └── models/            # Model weights & metadata
├── user/                  # Client tracking
│   └── models/            # Client model
├── mahjong_api/
│   ├── settings/          # Django settings
│   │   ├── base.py        # Shared config
│   │   ├── development.py # Local dev
│   │   ├── production.py  # Production
│   │   ├── test.py        # Tests (PostgreSQL via testcontainers)
│   │   └── ci.py          # CI jobs (SQLite, no Docker)
│   ├── env.py             # Environment variable loading
│   ├── celery.py          # Celery configuration
│   └── urls.py            # URL routing
├── .aws/                  # ECS task definitions
├── .circleci/             # CI configuration
├── Dockerfile
├── Pipfile
└── Pipfile.lock
```

## Deployment

### Docker Build

```bash
docker build -t mahjong-api .
docker run -p 8000:8000 --env-file .env mahjong-api
```

### AWS ECS

The project includes ECS Fargate task definitions in `.aws/`:

- `ecs-task-def.json` - Web service (Gunicorn)
- `ecs-worker-task-def.json` - Celery worker (downloads model from S3 on startup)

Secrets are stored in AWS Systems Manager Parameter Store under `/mahjong/`.

#### Model Loading

The Celery worker automatically downloads YOLO model weights from S3 at startup:
1. Worker starts and triggers `worker_init` signal
2. `model_loader.py` checks if model exists locally
3. If missing, downloads from `MODEL_S3_URI` to `MODEL_DIR`
4. Worker fails fast if download fails (ECS restarts container)

Required IAM permission for the ECS task role:
```json
{
    "Effect": "Allow",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::your-bucket/ml/models/*"
}
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `DJANGO_SECRET_KEY` | Yes | Django secret key |
| `AWS_ACCESS_KEY_ID` | Yes | AWS credentials |
| `AWS_SECRET_ACCESS_KEY` | Yes | AWS credentials |
| `AWS_STORAGE_BUCKET_NAME` | Yes | S3 bucket for uploads |
| `DJANGO_ENV` | No | `production`, `development`, `test`, or `ci` |
| `DJANGO_DEBUG` | No | Enable debug mode (default: True) |
| `DJANGO_ALLOWED_HOSTS` | No | Comma-separated hosts (default: *) |
| `AWS_REGION` | No | AWS region (default: ap-southeast-2) |
| `CELERY_BROKER_URL` | No | Celery broker (default: sqs://) |
| `MODEL_S3_URI` | No | S3 URI for model weights (worker only) |
| `MODEL_DIR` | No | Local model directory (default: /ml/models) |
| `TILE_DETECTOR_MODEL_NAME` | No | Model name (default: tile_detector) |
| `TILE_DETECTOR_MODEL_VERSION` | No | Model version (default: v0.1.0) |

## License

Proprietary - All rights reserved.
