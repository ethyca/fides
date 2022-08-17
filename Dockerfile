##############
## Frontend ##
##############
FROM node:16 as frontend

# Build the Ops frontend
WORKDIR /fidesops/clients/ops/admin-ui
COPY clients/ops/admin-ui/ .
RUN npm install
RUN npm run export

# Build the Ctl frontend
WORKDIR /fidesops/clients/ctl/admin-ui
COPY clients/ctl/admin-ui/ .
RUN npm install
RUN npm run export

#############
## Backend ##
#############
FROM --platform=linux/amd64 python:3.9.13-slim-bullseye as backend

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

ARG SKIP_MSSQL_INSTALLATION
RUN echo "ENVIRONMENT VAR:  SKIP_MSSQL_INSTALLATION $SKIP_MSSQL_INSTALLATION"

# SQL Server (MS SQL)
# https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server?view=sql-server-ver15
RUN if [ "$SKIP_MSSQL_INSTALLATION" != "true" ] ; then apt-get install -y --no-install-recommends apt-transport-https && apt-get clean && rm -rf /var/lib/apt/lists/* ; fi
RUN if [ "$SKIP_MSSQL_INSTALLATION" != "true" ] ; then curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - ; fi
RUN if [ "$SKIP_MSSQL_INSTALLATION" != "true" ] ; then curl https://packages.microsoft.com/config/debian/11/prod.list | tee /etc/apt/sources.list.d/msprod.list ; fi
RUN if [ "$SKIP_MSSQL_INSTALLATION" != "true" ] ; then apt-get update ; fi
ENV ACCEPT_EULA=y DEBIAN_FRONTEND=noninteractive
RUN if [ "$SKIP_MSSQL_INSTALLATION" != "true" ] ; then apt-get -y --no-install-recommends install \
    unixodbc-dev \
    msodbcsql17 \
    mssql-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* ; fi

#########################
## Python Dependencies ##
#########################
COPY mssql-requirements.txt .
RUN if [ "$SKIP_MSSQL_INSTALLATION" != "true" ] ; then pip --no-cache-dir install -r mssql-requirements.txt ; fi

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

# Make a static files directory
RUN mkdir -p /fides/src/fides/ops/build/static/
RUN mkdir -p /fides/src/fides/ctl/build/static/

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
RUN pip install dist/fidesctl-*.tar.gz

# Copy frontend build over
COPY --from=frontend /fidesops/clients/ops/admin-ui/out/ /fidesops/src/fidesops/ops/build/static/
COPY --from=frontend /fidesops/clients/ctl/admin-ui/out/ /fidesops/src/fidesops/ctl/build/static/
