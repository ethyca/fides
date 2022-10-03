# Pin to 3.10.6 to avoid a mypy error in 3.10.7
# If you update this, also update `DEFAULT_PYTHON_VERSION`
# in the GitHub workflow files
ARG PYTHON_VERSION="3.10.6"
ARG PLATFORM="linux/amd64"



##############
## Frontend ##
##############
FROM node:16 as frontend

# Build the admin-io frontend
WORKDIR /fides/clients/admin-ui
COPY clients/admin-ui/ .
RUN npm install
RUN npm run export

#############
## Backend ##
#############
# Don't force the platform by default
FROM --platform=${PLATFORM} python:${PYTHON_VERSION}-slim-bullseye as backend

# Install auxiliary software
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    make \
    vim \
    curl \
    g++ \
    gnupg \
    gcc \
    python3-wheel \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# SQL Server (MS SQL)
# https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server?view=sql-server-ver15
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/debian/11/prod.list | tee /etc/apt/sources.list.d/msprod.list
ENV ACCEPT_EULA=y DEBIAN_FRONTEND=noninteractive
RUN : \
    && apt-get update \
    && apt-get install \
    -y --no-install-recommends \
    apt-transport-https \
    unixodbc-dev \
    mssql-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

#########################
## Python Dependencies ##
#########################

COPY optional-requirements.txt .
RUN pip install -U pip --no-cache-dir install -r optional-requirements.txt

COPY dev-requirements.txt .
RUN pip install -U pip --no-cache-dir install -r dev-requirements.txt

COPY requirements.txt .
RUN pip install -U pip --no-cache-dir install -r requirements.txt

###############################
## General Application Setup ##
###############################
COPY . /fides
WORKDIR /fides

# Immediately flush to stdout, globally
ENV PYTHONUNBUFFERED=TRUE

# Reset the busted git cache
RUN git rm --cached -r .
RUN git reset --hard

# Enable detection of running within Docker
ENV RUNNING_IN_DOCKER=true

EXPOSE 8080
CMD [ "fides", "webserver" ]

#############################
## Development Application ##
#############################
FROM backend as dev

RUN pip install -e .

#############################
## Production Application ##
#############################
FROM backend as prod

# Install without a symlink
RUN python setup.py sdist
RUN pip install dist/ethyca-fides-*.tar.gz

# Copy frontend build over
COPY --from=frontend /fides/clients/admin-ui/out/ /fides/src/fides/ui-build/static/admin
