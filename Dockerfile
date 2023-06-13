# If you update this, also update `DEFAULT_PYTHON_VERSION` in the GitHub workflow files
ARG PYTHON_VERSION="3.10.11"

#########################
## Compile Python Deps ##
#########################
FROM python:${PYTHON_VERSION}-slim-bullseye as compile_image
ARG TARGETPLATFORM

# Install auxiliary software
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    g++ \
    git \
    gnupg \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Activate a Python venv
RUN python3 -m venv /opt/fides
ENV PATH="/opt/fides/bin:${PATH}"

# Install Python Dependencies
RUN pip --no-cache-dir --disable-pip-version-check install --upgrade pip setuptools wheel

COPY dangerous-requirements.txt .
RUN if [ $TARGETPLATFORM != linux/arm64 ] ; then pip install --no-cache-dir install -r dangerous-requirements.txt ; fi

COPY requirements.txt .
RUN pip install --no-cache-dir install -r requirements.txt

COPY dev-requirements.txt .
RUN pip install --no-cache-dir install -r dev-requirements.txt

##################
## Backend Base ##
##################
FROM python:${PYTHON_VERSION}-slim-bullseye as backend
ARG TARGETPLATFORM

# Loads compiled requirements and adds the to the path
COPY --from=compile_image /opt/fides /opt/fides
ENV PATH=/opt/fides/bin:$PATH

# These are all required for MSSQL
RUN : \
    && apt-get update \
    && apt-get install \
    -y --no-install-recommends \
    apt-transport-https \
    curl \
    git \
    gnupg \
    unixodbc-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# SQL Server (MS SQL)
# https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server?view=sql-server-ver15
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/debian/11/prod.list | tee /etc/apt/sources.list.d/msprod.list
ENV ACCEPT_EULA=y DEBIAN_FRONTEND=noninteractive
RUN if [ "$TARGETPLATFORM" != "linux/arm64" ] ; \
    then apt-get update \
    && apt-get install \
    -y --no-install-recommends \
    mssql-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* ; \
    fi

# General Application Setup ##
COPY . /fides
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
FROM backend as dev

RUN pip install -e . --no-deps

###################
## Frontend Base ##
###################
FROM node:16-alpine as frontend

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
FROM frontend as built_frontend

# Builds and exports admin-ui
RUN npm run export-admin-ui
# Builds privacy-center
RUN npm run build-privacy-center

###############################
## Production Privacy Center ##
###############################
FROM node:16-alpine as prod_pc

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
FROM backend as prod

# Copy frontend build over
COPY --from=built_frontend /fides/clients/admin-ui/out/ /fides/src/fides/ui-build/static/admin

# Install without a symlink
RUN python setup.py sdist
RUN pip install dist/ethyca-fides-*.tar.gz

# Remove this directory to prevent issues with catch all
RUN rm -r /fides/src/fides/ui-build
