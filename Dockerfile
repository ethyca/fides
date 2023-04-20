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
FROM node:16-alpine as frontend

RUN apk add --no-cache libc6-compat
# Build the frontend clients
WORKDIR /fides/clients
COPY clients/package.json ./
COPY clients/package-lock.json ./
COPY clients/fides-consent/package.json ./fides-consent/package.json
COPY clients/admin-ui/package.json ./admin-ui/package.json
COPY clients/privacy-center/package.json ./privacy-center/package.json

RUN npm install

COPY clients/ .

####################
## Built frontend ##
####################
FROM frontend as built_frontend

# Builds and exports admin-ui
RUN npm run export-ui
# Builds privacy-center
RUN npm run build-pc

#############################
## Production PC ##
#############################
FROM node:16-alpine as prod_pc

WORKDIR /fides/clients

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

#RUN addgroup --system --gid 1001 nodejs
#RUN adduser --system --uid 1001 nextjs
#
#RUN chown nextjs:nodejs /app

# We need to copy everything so we can rebuild with the new configs if needed
COPY --from=built_frontend /fides/clients /fides/clients
#RUN ln -s /fides/clients/privacy-center /app

WORKDIR /fides/clients/privacy-center
#COPY --from=built_frontend /fides/clients/privacy-center .

# The config directory is not needed unless it is mounted as a volume because the next
# build has already been run. By deleteing it we can check if is was added with a volume
# and we to rebuild with a custom config.
RUN rm -r config

RUN chmod +x start.sh

# todo- need to run as root so we can rebuild and copy PC over to /app. We want to eventually remove the rebuild entirely
#USER nextjs

EXPOSE 3000

CMD ["./start.sh"]

#############################
## Production Application ##
#############################
FROM backend as prod

# Copy frontend build over
COPY --from=built_frontend /fides/clients/admin-ui/out/ /fides/src/fides/ui-build/static/admin

# Install without a symlink
RUN python setup.py sdist
RUN pip install dist/ethyca-fides-*.tar.gz

# Remove this directory to prevent issues with catch all
RUN rm -r /fides/src/fides/ui-build
