# If you update this, also update `DEFAULT_PYTHON_VERSION` in the GitHub workflow files
ARG PYTHON_VERSION="3.13.11"
#########################
## Compile Python Deps ##
#########################
FROM python:${PYTHON_VERSION}-bookworm AS compile_image


# Install auxiliary software
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    g++ \
    git \
    gnupg \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# Install FreeTDS (used for PyMSSQL)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libssl-dev \
    libffi-dev \
    libkrb5-dev \
    unixodbc \
    unixodbc-dev \
    freetds-dev \
    freetds-bin \
    python-dev-is-python3 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv (standalone) and sync dependencies from pyproject.toml (no project, no dev, with optional [all])
WORKDIR /build
ENV UV_COMPILE_BYTECODE=0
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /bin/uv
COPY pyproject.toml uv.lock README.md ./
# Ensure setuptools is available so deps that use pkg_resources at build time (e.g. in setup.py) can be built
RUN uv venv && uv pip install setuptools wheel && uv sync --no-install-project --no-dev --extra all --locked

##################
## Backend Base ##
##################
FROM python:${PYTHON_VERSION}-slim-bookworm AS backend

# Add the fidesuser user but don't switch to it yet
RUN addgroup --system --gid 1001 fidesgroup
RUN adduser --system --uid 1001 --home /home/fidesuser fidesuser


RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    git \
    freetds-dev \
    freetds-bin \
    python-dev-is-python3 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Load compiled venv and uv binary from compile stage
COPY --from=compile_image /build/.venv /opt/fides
COPY --from=compile_image /bin/uv /bin/uv
ENV PATH=/opt/fides/bin:$PATH
# Use the pre-built venv so "uv run" in the container does not create/sync .venv (avoids C extension rebuilds)
ENV UV_PROJECT_ENVIRONMENT=/opt/fides
# In prod, /opt/fides stays root-owned (fidesuser can read/execute only). Dev stage chowns after editable install.

# General Application Setup ##
USER fidesuser

# This prevents getpwuid() crashes when running as non-default UIDs
ENV USER=fidesuser

COPY --chown=fidesuser:fidesgroup . /fides
WORKDIR /fides

# Immediately flush to stdout, globally
ENV PYTHONUNBUFFERED=TRUE

# Reset the busted git cache
RUN git rm --cached -r .

# This is a required workaround due to: https://github.com/ethyca/fides/issues/2440
RUN git config --global --add safe.directory /fides

# Export the version to a file for frontend use (hatch-vcs from git tags)
RUN uv venv /tmp/hatch-env && \
    uv pip install --python /tmp/hatch-env/bin/python hatch hatch-vcs && \
    cd /fides && /tmp/hatch-env/bin/hatch version > /fides/version.txt && \
    /opt/fides/bin/python -c "import json; v=open('/fides/version.txt').read().strip(); print(json.dumps({'version': v}))" > /fides/version.json && rm /fides/version.txt && rm -rf /tmp/hatch-env

# Enable detection of running within Docker
ENV RUNNING_IN_DOCKER=true

EXPOSE 8080
CMD [ "fides", "webserver" ]

#############################
## Development Application ##
#############################
FROM backend AS dev

USER root

# Editable install so the mounted /fides package is used at runtime; chown so fidesuser can run "uv run" (which may update this install)
RUN uv pip install --python /opt/fides/bin/python -e . --no-deps && \
    chown -R fidesuser:fidesgroup /opt/fides

USER fidesuser

###################
## Frontend Base ##
###################
FROM node:20-alpine AS frontend

RUN apk add --no-cache libc6-compat
# Build the frontend clients
WORKDIR /fides/clients
COPY clients/package.json clients/package-lock.json ./
COPY clients/fides-js/package.json ./fides-js/package.json
COPY clients/admin-ui/package.json ./admin-ui/package.json
COPY clients/privacy-center/package.json ./privacy-center/package.json

RUN npm ci

COPY clients/ .

####################
## Built frontend ##
####################
FROM frontend AS built_frontend

# IS_TEST enables test IDs in fides-js
ARG IS_TEST=false
ENV IS_TEST=$IS_TEST

# Imports the Fides package version from the backend
COPY --from=backend /fides/version.json ./version.json

# Builds and exports admin-ui
RUN npm run export-admin-ui
# Builds privacy-center
RUN npm run build-privacy-center

###############################
## Production Privacy Center ##
###############################
FROM node:20-alpine AS prod_pc

WORKDIR /fides/clients

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs
USER nextjs

COPY --from=built_frontend --chown=nextjs:nodejs /fides/clients .
WORKDIR /fides/clients/privacy-center

EXPOSE 3000

CMD ["npm", "run", "start"]

############################
## Production Application ##
############################
FROM backend AS prod

# Copy frontend build over
COPY --from=built_frontend /fides/clients/admin-ui/out/ /fides/src/fides/ui-build/static/admin
USER root
# Build sdist with uv and install
RUN cd /fides && uv build --sdist && \
    uv pip install --python /opt/fides/bin/python dist/ethyca_fides-*.tar.gz

# Remove this directory to prevent issues with catch all
RUN rm -r /fides/src/fides/ui-build
USER fidesuser

############################
## Test image (prod + writable venv for "uv run pytest" with mounted /fides)
############################
FROM prod AS test
USER root
RUN chown -R fidesuser:fidesgroup /opt/fides
USER fidesuser
