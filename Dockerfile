FROM --platform=linux/amd64 python:3.8-slim-buster as base

# Update pip in the base image since we'll use it everywhere
RUN pip install -U pip

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
    ipython \
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
RUN curl https://packages.microsoft.com/config/debian/10/prod.list | tee /etc/apt/sources.list.d/msprod.list
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

# Install without a symlink
RUN python setup.py sdist
RUN pip install dist/fidesctl-*.tar.gz
