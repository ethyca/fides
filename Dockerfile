##############
## Frontend ##
##############
FROM node:16 as frontend

WORKDIR /fidesops/clients/ops/admin-ui
COPY clients/ops/admin-ui/ .
RUN npm install
# Build the frontend static files
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

COPY dev-requirements.txt .
RUN pip install -U pip --no-cache-dir install -r dev-requirements.txt

COPY requirements.txt .
RUN pip install -U pip --no-cache-dir install -r requirements.txt

###############################
## General Application Setup ##
###############################
COPY . /fidesops
WORKDIR /fidesops

# Immediately flush to stdout, globally
ENV PYTHONUNBUFFERED=TRUE

# Enable detection of running within Docker
ENV RUNNING_IN_DOCKER=true

# Make a static files directory
RUN mkdir -p /fidesops/src/fidesops/build/static/

EXPOSE 8080
CMD [ "fidesops", "webserver" ]

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
RUN pip install dist/fidesops-*.tar.gz

# Copy frontend build over
COPY --from=frontend /fidesops/clients/ops/admin-ui/out/ /fidesops/src/fidesops/build/static/
