# Book Service — SFG

> A book and chapter management microservice. It handles EPUB uploads, stores metadata in PostgreSQL, stores files in S3/MinIO, and publishes search update events to RabbitMQ through TaskIQ.

---

## Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Technology](#technology)
- [Run](#run)
- [Environment Variables](#environment-variables)
- [API](#api)
- [Project Structure](#project-structure)

---

## Overview

Book Service is responsible for:

- CRUD operations for books and chapters
- EPUB uploads with parsing through `ebooklib` and `beautifulsoup4`
- File storage in MinIO through `aioboto3`, including presigned URLs
- Event publishing to RabbitMQ (`sfg.book-search-updates`) for search index updates

The service follows **Clean Architecture**: Domain → Application → Infrastructure → Presentation.

---

## Architecture

```text
HTTP Request → Presentation (FastAPI Router)
                    ↓
              Application (Use Cases)
                    ↓
              Domain (Entities, Protocols)
                    ↓
         Infrastructure (SQLAlchemy, S3, TaskIQ/RabbitMQ)
                    ↓
          PostgreSQL  +  MinIO  +  RabbitMQ
```

---

## Technology

| Package | Version | Role |
|-------|--------|------|
| `fastapi` | ^0.116.1 | HTTP framework |
| `sqlalchemy` | ^2.0.43 | ORM |
| `asyncpg` | ^0.30.0 | Async PostgreSQL driver |
| `alembic` | ^1.16.4 | Database migrations |
| `aioboto3` | ^15.1.0 | S3/MinIO client |
| `ebooklib` | ^0.19 | EPUB parsing |
| `beautifulsoup4` | ^4.13.5 | Chapter HTML parsing |
| `taskiq` + `taskiq-aio-pika` | ^0.11.18 | Background tasks through RabbitMQ |
| `loguru` | ^0.7.3 | Logging |
| Python | ≥ 3.12 | Runtime |

---

## Run

### Local development with Poetry

```bash
cd Backend/book-service
cp .env.example .env      # fill in the variables
poetry install
alembic upgrade head      # apply migrations
uvicorn main:app --reload --port 8001
```

### Docker

```bash
docker build -t sfg-book-service .
docker run -p 8001:8000 --env-file .env sfg-book-service
```

> **Dependencies:** PostgreSQL, MinIO, and RabbitMQ must be available before starting the service.

### Kubernetes / Minikube

```bash
eval $(minikube -p minikube docker-env)
docker build -t bookservice:latest .
kubectl apply -k k8s/overlays/minikube
```

The Kubernetes manifests are organized into folders:

- [k8s/base/shared/secret.yaml](k8s/base/shared/secret.yaml) — shared Secret for the application and infrastructure
- [k8s/base/infra/postgres](k8s/base/infra/postgres) — PostgreSQL
- [k8s/base/infra/rabbitmq](k8s/base/infra/rabbitmq) — RabbitMQ
- [k8s/base/infra/minio](k8s/base/infra/minio) — MinIO
- [k8s/base/apps/deployment.yaml](k8s/base/apps/deployment.yaml) — Book Service Deployment
- [k8s/base/apps/service.yaml](k8s/base/apps/service.yaml) — Book Service Service
- [k8s/overlays/minikube](k8s/overlays/minikube) — local cluster entrypoint

With this layout, a single `kubectl apply -k k8s/overlays/minikube` is enough. Kustomize assembles the full stack automatically.

For additional microservices, use the same pattern:

1. `Deployment` with the service image.
2. `Service` with a stable DNS name.
3. `Secret` or `ConfigMap` for service-specific configuration.
4. Shared infrastructure dependencies in a separate layer, not copied into each service.

For new services, create their own folders under `k8s/base/apps/<service-name>` and register them in `k8s/base/kustomization.yaml`.

This lets you start the infrastructure first and then deploy services on top of it one by one.


## API

### `GET /health`

```json
{ "status": "ok", "service": "book-service" }
```

### Books — `/books`

| Method | Path | Description |
|-------|------|----------|
| `GET` | `/books` | List books with pagination |
| `POST` | `/books` | Create a book by uploading an EPUB |
| `GET` | `/books/{book_id}` | Get a book by ID |
| `PUT` | `/books/{book_id}` | Update metadata |
| `DELETE` | `/books/{book_id}` | Delete a book |

### Chapters — `/chapters`

| Method | Path | Description |
|-------|------|----------|
| `GET` | `/chapters/{book_id}` | List chapters for a book |
| `GET` | `/chapters/{chapter_id}/content` | Get chapter content |

---

## Project Structure

```text
book-service/
├── main.py                   # FastAPI entrypoint
├── app/
│   ├── domain/               # Entities (Book, Chapter) and interfaces
│   ├── application/          # Use cases (business logic)
│   ├── infrastructure/
│   │   ├── database/         # SQLAlchemy engine, base, models
│   │   ├── models/           # book_model.py, chapter_model.py
│   │   ├── taskiq/           # Broker and event publishing tasks
│   │   └── di.py             # Dependency injection wiring
│   └── presentation/
│       ├── api/v1/
│       │   ├── book_controller.py
│       │   └── chapter_controller.py
│       └── api/depends.py    # FastAPI dependencies
├── alembic/                  # Database migrations
├── tests/                    # pytest tests
├── Dockerfile
└── pyproject.toml
```