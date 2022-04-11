FROM --platform=linux/amd64 python:3.8-slim-buster as base

# Update pip in the base image since we'll use it everywhere
RUN pip install -U pip

FROM base as builder
#######################
## Tool Installation ##
#######################

RUN apt-get update
RUN apt-get install -y \
    curl \
    git \
    ipython \
    make \
    vim \
    g++ \
    gnupg \
    gcc

###################
## Database Deps ##
###################

# Postgres
RUN apt-get -y install libpq-dev

# SQL Server (MS SQL)
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/debian/10/prod.list | tee /etc/apt/sources.list.d/msprod.list
RUN apt-get update
ENV ACCEPT_EULA=y DEBIAN_FRONTEND=noninteractive
RUN apt-get -y install \
    apt-transport-https \
    unixodbc-dev \
    mssql-tools

#################
## Python Deps ##
#################

COPY dev-requirements.txt dev-requirements.txt
RUN pip install --prefix=/install -r dev-requirements.txt

COPY requirements.txt requirements.txt
RUN pip install --prefix=/install -r requirements.txt

COPY optional_requirements.txt optional_requirements.txt
RUN pip install --prefix=/install -r optional_requirements.txt

############################
## Application Dev Setup ##
###########################
FROM base as dev
COPY --from=builder /install /usr/local

# This is required for pyodbc
RUN apt-get update
RUN apt-get -y install unixodbc
RUN apt-get clean -y

# Copy in the application files and install fidesctl locally
COPY . /fides/fidesctl
WORKDIR /fides/fidesctl
RUN pip install -e ".[all,mssql]"

# Immediately flush to stdout, globally
ENV PYTHONUNBUFFERED=TRUE

# Enable detection of running within Docker
ENV RUNNING_IN_DOCKER=TRUE

EXPOSE 8080
CMD ["fidesctl", "webserver"]

#############################
## Application Prod Setup ##
############################
FROM dev as prod

# Install without a symlink
RUN pip uninstall fidesctl -y
RUN python setup.py sdist
RUN pip install dist/fidesctl-*.tar.gz
