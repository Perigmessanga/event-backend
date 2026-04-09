FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Installer dépendances système
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        postgresql-client \
        libpq-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements et installer prod
COPY requirements /app/requirements
ARG REQUIREMENTS_FILE=requirements/production.txt
RUN pip install --no-cache-dir -r ${REQUIREMENTS_FILE}

# Copier le code
COPY . /app/

# Corriger fins de ligne Windows + permissions
RUN find /app/docker -name "*.sh" -exec sed -i 's/\r//' {} \; \
    && find /app/docker -name "*.sh" -exec chmod +x {} \;

EXPOSE 8000

# Lancer Gunicorn pour la prod
CMD ["sh", "/app/docker/prod/entry-point.sh"]