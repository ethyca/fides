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
FROM --platform=linux/amd64 python:3.10.7-slim-bullseye as backend

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

RUN : \
    && apt-get update \
    && apt-get install \
    -y --no-install-recommends \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    wget \
    curl \
    llvm \
    libncurses5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libffi-dev \
    liblzma-dev \
    mecab-ipadic-utf8 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV HOME="/root"

WORKDIR $HOME
RUN apt-get install -y git
RUN git clone --depth=1 https://github.com/pyenv/pyenv.git .pyenv
ENV PYENV_ROOT="$HOME/.pyenv"
ENV PATH="$PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH"

ARG python37="3.7.14"
ARG python38="3.8.14"
ARG python39="3.9.14"
ARG python310="3.10.7"

RUN pyenv install ${python37}
RUN pyenv install ${python38}
RUN pyenv install ${python39}
RUN pyenv install ${python310}

COPY optional-requirements.txt .
RUN pyenv global ${python37} ; pip install -U pip --no-cache-dir install -r optional-requirements.txt
RUN pyenv global ${python38} ; pip install -U pip --no-cache-dir install -r optional-requirements.txt
RUN pyenv global ${python39} ; pip install -U pip --no-cache-dir install -r optional-requirements.txt
RUN pyenv global ${python310} ; pip install -U pip --no-cache-dir install -r optional-requirements.txt

COPY dev-requirements.txt .
RUN pyenv global ${python37} ; pip install -U pip --no-cache-dir install -r dev-requirements.txt
RUN pyenv global ${python38} ; pip install -U pip --no-cache-dir install -r dev-requirements.txt
RUN pyenv global ${python39} ; pip install -U pip --no-cache-dir install -r dev-requirements.txt
RUN pyenv global ${python310} ; pip install -U pip --no-cache-dir install -r dev-requirements.txt

COPY requirements.txt .
RUN pyenv global ${python37} ; pip install -U pip --no-cache-dir install -r requirements.txt
RUN pyenv global ${python38} ; pip install -U pip --no-cache-dir install -r requirements.txt
RUN pyenv global ${python39} ; pip install -U pip --no-cache-dir install -r requirements.txt
RUN pyenv global ${python310} ; pip install -U pip --no-cache-dir install -r requirements.txt

RUN pyenv global ${python310}
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
COPY --from=frontend /fidesops/clients/ops/admin-ui/out/ /fidesops/src/fidesops/ops/build/static/
COPY --from=frontend /fidesops/clients/ctl/admin-ui/out/ /fidesops/src/fidesops/ctl/build/static/
