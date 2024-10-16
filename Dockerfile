# If you update this, also update `DEFAULT_PYTHON_VERSION` in the GitHub workflow files
ARG PYTHON_VERSION="3.10.13"
#########################
## Compile Python Deps ##
#########################
FROM python:${PYTHON_VERSION}-slim-bookworm AS compile_image


# Install auxiliary software
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
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
    libxslt-dev \
    libkrb5-dev \
    unixodbc \
    unixodbc-dev \
    freetds-dev \
    freetds-bin \
    python-dev-is-python3 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python Dependencies

COPY dev-requirements.txt .
RUN pip install --user -U pip --no-cache-dir -r dev-requirements.txt

# Activate a Python venv
RUN python3 -m venv /opt/fides
ENV PATH="/opt/fides/bin:${PATH}"

# Install Python Dependencies
RUN pip --no-cache-dir --disable-pip-version-check install --upgrade pip setuptools wheel

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY optional-requirements.txt .
RUN pip install --no-cache-dir -r optional-requirements.txt

COPY dev-requirements.txt .
RUN pip install --no-cache-dir -r dev-requirements.txt

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

# Loads compiled requirements and adds the to the path
COPY --from=compile_image /opt/fides /opt/fides
ENV PATH=/opt/fides/bin:$PATH

# General Application Setup ##
USER fidesuser
COPY --chown=fidesuser:fidesgroup . /fides
WORKDIR /fides

# Immediately flush to stdout, globally
ENV PYTHONUNBUFFERED=TRUE

# Reset the busted git cache
RUN git rm --cached -r .

# This is a required workaround due to: https://github.com/ethyca/fides/issues/2440
RUN git config --global --add safe.directory /fides

# Enable detection of running within Docker
ENV RUNNING_IN_DOCKER=true

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
# Build the frontend clients
WORKDIR /fides/clients
COPY clients/package.json clients/package-lock.json ./
COPY clients/fides-js/package.json ./fides-js/package.json
COPY clients/admin-ui/package.json ./admin-ui/package.json
COPY clients/privacy-center/package.json ./privacy-center/package.json

RUN npm install

COPY clients/ .

####################
## Built frontend ##
####################
FROM frontend AS built_frontend

# Builds and exports admin-ui
RUN npm run export-admin-ui
# Builds privacy-center
RUN npm run build-privacy-center

###############################
## Production Privacy Center ##
###############################
FROM node:20-alpine AS prod_pc

WORKDIR /fides/clients

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

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
# Install without a symlink
RUN python setup.py sdist

# USER root commented out for debugging
RUN pip install dist/ethyca_fides-*.tar.gz

# Remove this directory to prevent issues with catch all
RUN rm -r /fides/src/fides/ui-build
USER fidesuser
