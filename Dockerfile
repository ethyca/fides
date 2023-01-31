# If you update this, also update `DEFAULT_PYTHON_VERSION` in the GitHub workflow files
ARG PYTHON_VERSION="3.10.7"


#########################
## Compile Python Deps ##
#########################
FROM python:${PYTHON_VERSION}-slim-bullseye as compile_image
ARG TARGETPLATFORM

# Install auxiliary software
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    g++ \
    gnupg \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python Dependencies
COPY dangerous-requirements.txt .
RUN if [ $TARGETPLATFORM != linux/arm64 ] ; then pip install --user -U pip --no-cache-dir install -r dangerous-requirements.txt ; fi

COPY dev-requirements.txt .
RUN pip install --user -U pip --no-cache-dir install -r dev-requirements.txt

COPY requirements.txt .
RUN pip install --user -U pip --no-cache-dir install -r requirements.txt

##################
## Backend Base ##
##################
FROM python:${PYTHON_VERSION}-slim-bullseye as backend
ARG TARGETPLATFORM

# Loads compiled requirements and adds the to the path
COPY --from=compile_image /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

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
FROM node:16-slim as frontend

# Build the admin-ui frontend
WORKDIR /fides/clients/admin-ui
COPY clients/admin-ui/package.json clients/admin-ui/package-lock.json ./
RUN npm install
COPY clients/admin-ui/ .
RUN npm run export

#############################
## Production Application ##
#############################
FROM backend as prod

# Copy frontend build over
COPY --from=frontend /fides/clients/admin-ui/out/ /fides/src/fides/ui-build/static/admin

# Install without a symlink
RUN python setup.py sdist
RUN pip install dist/ethyca-fides-*.tar.gz
