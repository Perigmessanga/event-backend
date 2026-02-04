# ==============================
# Global config
# ==============================

PROJECT_NAME := event api
ENV ?= dev

COMPOSE := docker compose
COMPOSE_FILE := compose.$(ENV).yml
ENV_FILE := .env.$(ENV)

DJANGO := django
# CELERY := celery
# CELERY_BEAT := celery-beat

.DEFAULT_GOAL := help

# ==============================
# Safety
# ==============================

guard-prod:
ifeq ($(ENV),prod)
	@echo "ERROR: This command is blocked in production"
	@exit 1
endif

# ==============================
# Core Docker
# ==============================

build:
	$(COMPOSE) --env-file $(ENV_FILE) -f $(COMPOSE_FILE) build

up:
	$(COMPOSE) --env-file $(ENV_FILE) -f $(COMPOSE_FILE) up

up-d:
	$(COMPOSE) --env-file $(ENV_FILE) -f $(COMPOSE_FILE) up -d

down:
	$(COMPOSE) -f $(COMPOSE_FILE) down

down-v: guard-prod
	$(COMPOSE) -f $(COMPOSE_FILE) down -v

restart:
	$(MAKE) down
	$(MAKE) up

logs:
	$(COMPOSE) -f $(COMPOSE_FILE) logs -f

ps:
	$(COMPOSE) -f $(COMPOSE_FILE) ps

# ==============================
# Django
# ==============================

shell:
	$(COMPOSE) -f $(COMPOSE_FILE) exec $(DJANGO) python manage.py shell

runserver:
	$(COMPOSE) -f $(COMPOSE_FILE) exec $(DJANGO) python manage.py runserver 0.0.0.0:8000

migrate:
	$(COMPOSE) -f $(COMPOSE_FILE) exec $(DJANGO) python manage.py migrate

makemigrations:
	$(COMPOSE) -f $(COMPOSE_FILE) exec $(DJANGO) python manage.py makemigrations

superuser:
	$(COMPOSE) -f $(COMPOSE_FILE) exec $(DJANGO) python manage.py createsuperuser

collectstatic:
	$(COMPOSE) -f $(COMPOSE_FILE) exec $(DJANGO) python manage.py collectstatic --noinput

test:
	$(COMPOSE) -f $(COMPOSE_FILE) exec $(DJANGO) python manage.py test

# ==============================
# Celery
# ==============================

# celery-logs:
# 	$(COMPOSE) -f $(COMPOSE_FILE) logs -f $(CELERY)

# beat-logs:
# 	$(COMPOSE) -f $(COMPOSE_FILE) logs -f $(CELERY_BEAT)

# celery-shell:
# 	$(COMPOSE) -f $(COMPOSE_FILE) exec $(CELERY) sh

# ==============================
# Database
# ==============================

db-shell:
	$(COMPOSE) -f $(COMPOSE_FILE) exec postgres psql -U $$DB_USER -d $$DB_NAME

# ==============================
# Maintenance
# ==============================

clean: guard-prod
	$(COMPOSE) -f $(COMPOSE_FILE) down -v --remove-orphans
	docker system prune -f

reset: guard-prod
	$(MAKE) down-v
	$(MAKE) build
	$(MAKE) up

# ==============================
# Help
# ==============================

help:
	@echo ""
	@echo "Usage:"
	@echo "  make <command> ENV=dev|test|prod"
	@echo ""
	@echo "Examples:"
	@echo "  make up ENV=dev"
	@echo "  make test ENV=test"
	@echo "  make build ENV=prod"
	@echo ""
	@echo "Commands:"
	@echo "  build, up, up-d, down, restart, logs, ps"
	@echo "  migrate, makemigrations, superuser, test"
# 	@echo "  celery-logs, beat-logs"
	@echo "  db-shell"
	@echo "  clean, reset"
	@echo ""