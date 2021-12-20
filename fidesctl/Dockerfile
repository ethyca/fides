FROM python:3.8-slim-buster

######################
# Tool Installation ##
######################

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

###########################
## Database Dependencies ##
###########################

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

#######################
## Application Setup ##
#######################

# Install Requirements
RUN pip install -U pip

COPY dev-requirements.txt dev-requirements.txt
RUN pip install -r dev-requirements.txt

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy in the application files and install fidesctl locally
COPY . /fides/fidesctl
WORKDIR /fides/fidesctl
RUN pip install -e ".[all]"

# Immediately flush to stdout, globally
ENV PYTHONUNBUFFERED=TRUE

EXPOSE 8080
CMD ["fidesctl", "webserver"]
