FROM --platform=linux/amd64 python:3.8-slim-bullseye as base

# Update pip in the base image since we'll use it everywhere
RUN pip install -U pip

####################
## Build frontend ##
####################
FROM node:16 as frontend

WORKDIR /fides/clients/admin-ui

# install node modules
COPY clients/admin-ui/ .
RUN npm install

# Build the frontend static files
RUN npm run export

#######################
## Tool Installation ##
#######################

FROM base as builder

RUN : \
    && apt-get update \
    && apt-get install \
    -y --no-install-recommends \
    curl \
    git \
    vim \
    g++ \
    gnupg \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

###########################
## Database Dependencies ##
###########################

# Postgres
RUN : \
    && apt-get update \
    && apt-get install \
    -y --no-install-recommends \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# SQL Server (MS SQL)
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

COPY dev-requirements.txt dev-requirements.txt
RUN pip install -r dev-requirements.txt

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY optional-requirements.txt optional-requirements.txt
RUN pip install -r optional-requirements.txt

###############################
## General Application Setup ##
###############################

COPY . /fides
WORKDIR /fides

# Reset the busted git cache
RUN git rm --cached -r .
RUN git reset --hard

# Immediately flush to stdout, globally
ENV PYTHONUNBUFFERED=TRUE

# Enable detection of running within Docker
ENV RUNNING_IN_DOCKER=TRUE

EXPOSE 8080
CMD ["fidesctl", "webserver"]

###################################
## Application Development Setup ##
###################################

FROM builder as dev

# Install fidesctl as a symlink
RUN pip install -e ".[all,mssql]"

##################################
## Production Application Setup ##
##################################

FROM builder as prod

# Copy frontend build over in order to be available in wheel package
COPY --from=frontend /fides/clients/admin-ui/out/ /fides/src/fidesctl/ui-build/static/admin/

# Install without a symlink
RUN python setup.py bdist_wheel 
RUN pip install dist/fidesctl-*.whl
