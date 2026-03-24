# ==============================
# Global config
# ==============================

PROJECT_NAME := event-api
ENV ?= dev

COMPOSE      := docker compose
COMPOSE_FILE := compose.$(ENV).yml
ENV_FILE     := .env.$(ENV)

DJANGO       := web

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

logs-web:
	$(COMPOSE) -f $(COMPOSE_FILE) logs -f $(DJANGO)

ps:
	$(COMPOSE) -f $(COMPOSE_FILE) ps

# ==============================
# Django
# ==============================

shell:
	$(COMPOSE) -f $(COMPOSE_FILE) exec $(DJANGO) python manage.py shell

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
# Database
# ==============================

db-shell:
	$(COMPOSE) -f $(COMPOSE_FILE) exec postgres psql -U $${POSTGRES_USER} -d $${POSTGRES_DB}

db-backup:
	$(COMPOSE) -f $(COMPOSE_FILE) exec postgres pg_dump -U $${POSTGRES_USER} $${POSTGRES_DB} > backup_$$(date +%Y%m%d_%H%M%S).sql

# ==============================
# Maintenance
# ==============================

clean: guard-prod
	$(COMPOSE) -f $(COMPOSE_FILE) down -v --remove-orphans
	docker system prune -f

reset: guard-prod
	$(MAKE) down-v
	$(MAKE) build
	$(MAKE) up-d
	$(MAKE) migrate

# ==============================
# Help
# ==============================

help:
	@echo ""
	@echo "Usage:"
	@echo "  make <command> ENV=dev|prod"
	@echo ""
	@echo "Examples:"
	@echo "  make up ENV=dev"
	@echo "  make migrate ENV=dev"
	@echo "  make build ENV=prod"
	@echo ""
	@echo "Commands:"
	@echo "  build          Build les images Docker"
	@echo "  up             Démarrer les containers (foreground)"
	@echo "  up-d           Démarrer les containers (background)"
	@echo "  down           Arrêter les containers"
	@echo "  down-v         Arrêter + supprimer volumes (bloqué en prod)"
	@echo "  restart        Redémarrer"
	@echo "  logs           Logs de tous les containers"
	@echo "  logs-web       Logs du container Django"
	@echo "  ps             Status des containers"
	@echo "  migrate        Lancer les migrations"
	@echo "  makemigrations Créer les migrations"
	@echo "  superuser      Créer un superutilisateur"
	@echo "  collectstatic  Collecter les fichiers statiques"
	@echo "  test           Lancer les tests"
	@echo "  db-shell       Shell Postgres"
	@echo "  db-backup      Backup de la base de données"
	@echo "  clean          Nettoyer tout (bloqué en prod)"
	@echo "  reset          Reset complet (bloqué en prod)"
	@echo ""