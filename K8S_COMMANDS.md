# Kubernetes — Шпаргалка по командам и архитектуре

> Гайд для локальной разработки на **Minikube**.
> Все команды выполняются из корня проекта (`~/spaced-repetition-bot`).

---

## Оглавление

- [Первоначальная настройка](#первоначальная-настройка)
- [Сборка образов](#сборка-образов)
- [Деплой в кластер](#деплой-в-кластер)
- [Просмотр и отладка](#просмотр-и-отладка)
- [Проброс портов (port-forward)](#проброс-портов-port-forward)
- [Удаление ресурсов](#удаление-ресурсов)
- [Полезные комбинации](#полезные-комбинации)
- [Структура k8s/ — описание файлов](#структура-k8s--описание-файлов)
- [Как запустить все микросервисы вместе](#как-запустить-все-микросервисы-вместе)

---

## Первоначальная настройка

```bash
# Запуск Minikube (если ещё не запущен)
minikube start

# ⚠️ ВАЖНО: Переключить Docker на демон Minikube
# Без этого образы соберутся в вашем локальном Docker, а Minikube их не увидит!
eval $(minikube docker-env)

# Проверить, что Docker указывает на Minikube
docker info | grep -i name
```

> **Примечание:** `eval $(minikube docker-env)` нужно выполнять в **каждом новом терминале**.

---

## Сборка образов

### Один сервис

```bash
# Формат
docker build -t <имя-образа>:<тег> <путь-к-Dockerfile>

# Примеры
docker build -t bookservice:latest        ./Backend/book-service
docker build -t api-gateway:latest        ./Backend/api-gateway
docker build -t identity-service:latest   ./Backend/identity-service
docker build -t reader-service:latest     ./Backend/reader-service
docker build -t search-service:latest     ./Backend/search-service
docker build -t translation-service:latest ./Backend/translation-service
docker build -t learning-service:latest   ./Backend/learning-service
docker build -t bot-service:latest        ./bot-service
docker build -t frontend:latest           ./Frontend
```

### Все сервисы разом

```bash
# Быстрый скрипт для пересборки всех образов
for svc in book-service api-gateway identity-service reader-service \
           search-service translation-service learning-service; do
  echo "🔨 Building $svc..."
  docker build -t "$svc:latest" "./Backend/$svc"
done

docker build -t bot-service:latest ./bot-service
docker build -t frontend:latest   ./Frontend

echo "✅ Все образы собраны"
```

### Проверить собранные образы

```bash
# Все образы в Minikube
docker images

# Только ваши
docker images | grep -E "bookservice|api-gateway|identity|reader|search|translation|learning|bot-service|frontend"
```

---

## Деплой в кластер

### Через Kustomize (рекомендуется)

```bash
# Применить все манифесты book-service (инфра + приложение)
kubectl apply -k ./Backend/book-service/k8s/minikube

# Посмотреть, что Kustomize сгенерирует (без применения)
kubectl kustomize ./Backend/book-service/k8s/minikube
```

### Через отдельные YAML-файлы

```bash
# Применить один файл
kubectl apply -f ./Backend/book-service/k8s/base/apps/deployment.yaml

# Применить всю директорию
kubectl apply -f ./Backend/book-service/k8s/base/apps/
```

### Перезапуск деплоймента (например, после пересборки образа)

```bash
# Перезапустить поды без изменения манифестов
kubectl rollout restart deployment book-service

# Следить за ходом обновления
kubectl rollout status deployment book-service
```

---

## Просмотр и отладка

### Поды

```bash
# Список всех подов
kubectl get pods

# Следить за подами в реальном времени
kubectl get pods -w

# Подробная информация о поде (образ, события, ошибки)
kubectl describe pod <имя-пода>
# Пример: kubectl describe pod book-service-6d6dd94b77-7b7gv

# Логи пода
kubectl logs <имя-пода>

# Логи init-контейнера (миграции)
kubectl logs <имя-пода> -c run-migrations

# Логи в реальном времени (follow)
kubectl logs -f <имя-пода>

# Логи предыдущего упавшего контейнера
kubectl logs <имя-пода> --previous

# Зайти внутрь контейнера
kubectl exec -it <имя-пода> -- /bin/sh
```

### Деплойменты

```bash
# Список деплойментов
kubectl get deployments

# Подробности деплоймента
kubectl describe deployment book-service

# История ревизий
kubectl rollout history deployment book-service
```

### Сервисы, секреты, PVC

```bash
# Все сервисы
kubectl get svc

# Все секреты
kubectl get secrets

# Посмотреть значения секрета (декодированные)
kubectl get secret book-service-secrets -o jsonpath='{.data}' | jq -r 'to_entries[] | "\(.key): \(.value | @base64d)"'

# Persistent Volume Claims
kubectl get pvc
```

### Все ресурсы разом

```bash
kubectl get all
```

---

## Проброс портов (port-forward)

`kubectl port-forward` пробрасывает порт из кластера на ваш `localhost`.

### Основные команды

```bash
# Формат
kubectl port-forward svc/<сервис> <локальный-порт>:<порт-в-кластере>

# book-service API
kubectl port-forward svc/book-service 8000:8000

# PostgreSQL (для подключения через DBeaver, psql и т.д.)
kubectl port-forward svc/postgres 5432:5432

# RabbitMQ Management UI
kubectl port-forward svc/rabbitmq 15672:15672

# MinIO Console
kubectl port-forward svc/minio 9001:9001

# MinIO S3 API
kubectl port-forward svc/minio 9000:9000
```

### Проброс нескольких портов одновременно

Каждый `port-forward` занимает терминал, поэтому запускайте их в фоне:

```bash
# Запустить все пробросы в фоне
kubectl port-forward svc/book-service 8000:8000 &
kubectl port-forward svc/postgres 5432:5432 &
kubectl port-forward svc/rabbitmq 15672:15672 &
kubectl port-forward svc/minio 9001:9001 &

# Проверить, что работают
jobs

# Остановить все фоновые пробросы
kill $(jobs -p)
```

### Проброс на нод (через minikube service)

```bash
# Открыть сервис через Minikube (создаст туннель автоматически)
minikube service book-service --url
```

---

## Удаление ресурсов

### Удалить поды

```bash
# Удалить конкретный под (деплоймент создаст новый автоматически)
kubectl delete pod <имя-пода>

# Удалить все поды по лейблу
kubectl delete pods -l app=book-service

# Принудительно удалить зависший под
kubectl delete pod <имя-пода> --force --grace-period=0
```

### Удалить деплоймент

```bash
# Удалить один деплоймент (удалит и все его поды)
kubectl delete deployment book-service

# Удалить все деплойменты
kubectl delete deployments --all
```

### Удалить всё, что создал Kustomize

```bash
# ⚠️ Удалит ВСЁ: приложение + PostgreSQL + RabbitMQ + MinIO + секреты
kubectl delete -k ./Backend/book-service/k8s/minikube
```

### Удалить по типу

```bash
kubectl delete svc book-service       # Сервис
kubectl delete secret book-service-secrets  # Секрет
kubectl delete pvc postgres-data      # PVC (⚠️ удалит данные!)
```

### Полная очистка namespace

```bash
# ⚠️ Осторожно: удалит ВСЁ в namespace default
kubectl delete all --all -n default
kubectl delete secrets --all -n default
kubectl delete pvc --all -n default
```

---

## Полезные комбинации

```bash
# 🔄 Пересобрать и передеплоить сервис
docker build -t bookservice:latest ./Backend/book-service && \
kubectl rollout restart deployment book-service

# 🩺 Быстрая диагностика: почему под не запускается?
kubectl describe pod <имя-пода> | tail -20

# 📊 Потребление ресурсов
kubectl top pods
kubectl top nodes

# 🔍 Найти поды по лейблу
kubectl get pods -l app=book-service -o wide

# 🧹 Удалить Evicted-поды
kubectl delete pods --field-selector=status.phase=Failed
```

---

## Структура k8s/ — описание файлов

```
k8s/
├── base/                         # Базовые манифесты (общие для всех сред)
│   ├── kustomization.yaml        # 📋 Список всех ресурсов для Kustomize
│   ├── apps/                     # Манифесты приложения
│   │   ├── deployment.yaml       # 🚀 Deployment
│   │   └── service.yaml          # 🌐 Service
│   ├── infra/                    # Манифесты инфраструктуры
│   │   ├── postgres/
│   │   │   ├── deployment.yaml   # 🐘 PostgreSQL Deployment
│   │   │   ├── service.yaml      # 🌐 PostgreSQL Service
│   │   │   └── pvc.yaml          # 💾 PostgreSQL PVC
│   │   ├── rabbitmq/
│   │   │   ├── deployment.yaml   # 🐰 RabbitMQ Deployment
│   │   │   └── service.yaml      # 🌐 RabbitMQ Service
│   │   └── minio/
│   │       ├── deployment.yaml   # 📦 MinIO Deployment
│   │       ├── service.yaml      # 🌐 MinIO Service
│   │       └── pvc.yaml          # 💾 MinIO PVC
│   └── shared/
│       └── secret.yaml           # 🔑 Secret
├── minikube/
│   └── kustomization.yaml        # 📋 Overlay для Minikube
└── overlays/                     # 📂 Overlay'и для других сред (пока пусто)
```

### Что делает каждый тип файла

| Файл | Что это | Зачем нужен |
|------|---------|-------------|
| **`deployment.yaml`** | Deployment | Описывает **как запускать** контейнеры: какой образ, сколько реплик, ресурсы (CPU/RAM), probes (проверки здоровья), init-контейнеры (миграции), стратегию обновления |
| **`service.yaml`** | Service | Создаёт **стабильный DNS-адрес** для доступа к подам внутри кластера. Например, `book-service:8000` — другие сервисы обращаются по этому имени |
| **`secret.yaml`** | Secret | Хранит **секретные данные**: пароли БД, API-токены, ключи. Передаются в контейнеры через `envFrom` |
| **`pvc.yaml`** | PersistentVolumeClaim | Запрашивает **постоянное хранилище** для данных (БД, файлы MinIO). Данные сохраняются при перезапуске подов |
| **`kustomization.yaml`** | Kustomize конфиг | Описывает **какие ресурсы применить** и позволяет делать overlay'и для разных сред (dev/staging/prod) |

### Ключевые концепции в deployment.yaml

| Секция | Что делает |
|--------|-----------|
| `replicas` | Сколько копий пода запускать |
| `strategy: RollingUpdate` | При обновлении сначала поднимает новый под, потом убивает старый (zero-downtime) |
| `initContainers` | Контейнеры, которые выполняются **до** основного (например, миграции БД) |
| `envFrom: secretRef` | Загружает **все** ключи из Secret как переменные окружения |
| `startupProbe` | Проверяет, что приложение **запустилось** (даёт время на инициализацию) |
| `livenessProbe` | Проверяет, что приложение **живо** (перезапускает, если зависло) |
| `readinessProbe` | Проверяет, что приложение **готово принимать трафик** |
| `resources.requests` | Минимум ресурсов, который K8s **гарантирует** поду |
| `resources.limits` | Максимум ресурсов, который под **не может превысить** |
| `securityContext` | Ограничения безопасности (не root, read-only FS, drop capabilities) |

---

## Как запустить все микросервисы вместе

### Текущее состояние проекта

| Сервис | Dockerfile | K8s-манифесты |
|--------|:----------:|:-------------:|
| book-service | ✅ | ✅ |
| api-gateway | ✅ | ❌ |
| identity-service | ✅ | ❌ |
| reader-service | ✅ | ❌ |
| search-service | ✅ | ❌ |
| translation-service | ✅ | ❌ |
| learning-service | ✅ | ❌ |
| bot-service | ✅ | ❌ |
| Frontend | ✅ | ❌ |

> K8s-манифесты пока есть только у **book-service**.
> Для полноценного запуска всех сервисов нужно создать аналогичные манифесты для каждого.

### Стратегия: как всё связать

Когда все сервисы будут в кластере, они смогут общаться **по DNS-именам сервисов**:

```
api-gateway      → http://book-service:8000
                 → http://identity-service:8000
                 → http://reader-service:8000
                 → ...

Frontend (Nginx) → http://api-gateway:8000   (через reverse proxy)
```

### Как прокидывать порты для всего проекта

**Вариант 1: `port-forward` — для разработки (просто, но вручную)**

```bash
# Прокинуть только фронтенд и API Gateway — этого обычно хватает
kubectl port-forward svc/frontend 3000:80 &
kubectl port-forward svc/api-gateway 8000:8000 &
# Открыть http://localhost:3000
```

> Внутри кластера сервисы и так видят друг друга по DNS.
> Прокидывать каждый микросервис **не нужно** — достаточно прокинуть точку входа (frontend + api-gateway).

**Вариант 2: Ingress — для продакшена (рекомендуется)**

Ingress — это единая точка входа в кластер, которая маршрутизирует трафик по URL-путям:

```bash
# Установить Ingress Controller в Minikube
minikube addons enable ingress
```

Пример Ingress-ресурса:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
spec:
  rules:
    - host: app.local
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: api-gateway
                port:
                  number: 8000
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend
                port:
                  number: 80
```

```bash
# Добавить домен в /etc/hosts
echo "$(minikube ip) app.local" | sudo tee -a /etc/hosts

# Открыть http://app.local
```

**Вариант 3: `minikube tunnel` — для LoadBalancer-сервисов**

```bash
# Запустить в отдельном терминале (требует sudo)
minikube tunnel

# Теперь сервисы типа LoadBalancer получат внешний IP
kubectl get svc
```

### Рекомендуемый порядок запуска всех сервисов

```bash
# 1. Переключить Docker на Minikube
eval $(minikube docker-env)

# 2. Собрать все образы
docker build -t bookservice:latest        ./Backend/book-service
docker build -t api-gateway:latest        ./Backend/api-gateway
docker build -t identity-service:latest   ./Backend/identity-service
docker build -t reader-service:latest     ./Backend/reader-service
docker build -t search-service:latest     ./Backend/search-service
docker build -t translation-service:latest ./Backend/translation-service
docker build -t learning-service:latest   ./Backend/learning-service
docker build -t bot-service:latest        ./bot-service
docker build -t frontend:latest           ./Frontend

# 3. Задеплоить инфраструктуру + book-service
kubectl apply -k ./Backend/book-service/k8s/minikube

# 4. Задеплоить остальные сервисы (когда будут манифесты)
# kubectl apply -k ./Backend/api-gateway/k8s/minikube
# kubectl apply -k ./Backend/identity-service/k8s/minikube
# ...

# 5. Прокинуть точки входа
kubectl port-forward svc/api-gateway 8000:8000 &
kubectl port-forward svc/frontend 3000:80 &
```
