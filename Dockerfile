##############
## Frontend ##
##############
FROM node:16 as frontend

WORKDIR /fidesops/clients/admin-ui
COPY clients/admin-ui/ .
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

# Update pip and install requirements
COPY requirements.txt dev-requirements.txt mssql-requirements.txt ./
RUN pip install -U pip  \
    && pip --no-cache-dir install -r requirements.txt -r dev-requirements.txt \
    && if [ "$SKIP_MSSQL_INSTALLATION" != "true" ] ; then pip --no-cache-dir install -r mssql-requirements.txt ; fi

# Copy in the application files and install it locally
COPY . /fidesops
WORKDIR /fidesops
RUN pip install -e .

# Enable detection of running within Docker
ENV RUNNING_IN_DOCKER=true

############
## Worker ##
############
FROM backend as worker
CMD [ "fidesops", "worker" ]

#################
## Application ##
#################
## Set the image up to be the application
FROM backend as app

# Make a static files directory
RUN mkdir -p /fidesops/src/fidesops/build/static/

# Copy frontend build over
COPY --from=frontend /fidesops/clients/admin-ui/out/ /fidesops/src/fidesops/build/static/

CMD [ "fidesops", "webserver" ]
