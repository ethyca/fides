# syntax=docker/dockerfile:1.4
# If you update this, also update `DEFAULT_PYTHON_VERSION` in the GitHub workflow files
ARG PYTHON_VERSION="3.10.13"

#########################
## Compile Python Deps ##
#########################
FROM python:${PYTHON_VERSION}-slim-bookworm AS compile_image

# Install all system dependencies in a single layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        g++ \
        git \
        gnupg \
        gcc \
        libssl-dev \
        libffi-dev \
        libxslt-dev \
        libkrb5-dev \
        unixodbc \
        unixodbc-dev \
        freetds-dev \
        freetds-bin \
        python-dev-is-python3 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Activate a Python venv
RUN python3 -m venv /opt/fides
ENV PATH="/opt/fides/bin:${PATH}"

# Install Python dependencies - copying all requirements files at once
COPY requirements.txt optional-requirements.txt dev-requirements.txt ./

# Use BuildKit cache for pip
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    pip install -r optional-requirements.txt && \
    pip install -r dev-requirements.txt

##################
## Backend Base ##
##################
FROM python:${PYTHON_VERSION}-slim-bookworm AS backend

# Add the fidesuser user but don't switch to it yet
RUN addgroup --system --gid 1001 fidesgroup && \
    adduser --system --uid 1001 --home /home/fidesuser fidesuser

# Install runtime dependencies in a single layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        git \
        freetds-dev \
        freetds-bin \
        python-dev-is-python3 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Loads compiled requirements and adds them to the path
COPY --from=compile_image /opt/fides /opt/fides
ENV PATH=/opt/fides/bin:$PATH

# General Application Setup
USER fidesuser
WORKDIR /fides

# Immediately flush to stdout, globally
ENV PYTHONUNBUFFERED=TRUE
# Enable detection of running within Docker
ENV RUNNING_IN_DOCKER=true

# Copy application code - do this later to maximize cache hits
COPY --chown=fidesuser:fidesgroup . .

# Reset the busted git cache and configure git
RUN git rm --cached -r . || true && \
    git config --global --add safe.directory /fides

EXPOSE 8080
CMD [ "fides", "webserver" ]

#############################
## Development Application ##
#############################
FROM backend AS dev

USER root
RUN pip install -e . --no-deps
USER fidesuser

###################
## Frontend Base ##
###################
FROM node:20-alpine AS frontend

RUN apk add --no-cache libc6-compat

# Install npm dependencies with improved caching
WORKDIR /fides/clients

# Copy package files first to leverage layer caching
COPY clients/package.json clients/package-lock.json ./
COPY clients/fides-js/package.json ./fides-js/
COPY clients/admin-ui/package.json ./admin-ui/
COPY clients/privacy-center/package.json ./privacy-center/

# Use BuildKit cache for node_modules
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# Copy the rest of the frontend code
COPY clients/ .

####################
## Built frontend ##
####################
FROM frontend AS built_frontend

# Build fides-js first (dependency for other packages)
WORKDIR /fides/clients/fides-js
RUN npm run build

# Build the admin UI and privacy center
WORKDIR /fides/clients
# Run builds in parallel if possible
RUN npm run export-admin-ui & \
    npm run build-privacy-center & \
    wait

###############################
## Production Privacy Center ##
###############################
FROM node:20-alpine AS prod_pc

WORKDIR /fides/clients

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

USER nextjs

COPY --from=built_frontend --chown=nextjs:nodejs /fides/clients .
WORKDIR /fides/clients/privacy-center

EXPOSE 3000

CMD ["npm", "run", "start"]

############################
## Production Application ##
############################
FROM backend AS prod

# Copy frontend build over - make sure directory exists first
USER root
RUN mkdir -p /fides/src/fides/ui-build/static/admin
COPY --from=built_frontend /fides/clients/admin-ui/out/ /fides/src/fides/ui-build/static/admin/

# Build and install the package
WORKDIR /fides

RUN python -m pip install --upgrade pip setuptools wheel && \
    python setup.py sdist && \
    pip install dist/ethyca_fides-*.tar.gz && \
    # Only remove ui-build directory if it exists
    if [ -d "/fides/src/fides/ui-build" ]; then rm -rf /fides/src/fides/ui-build; fi

USER fidesuser
