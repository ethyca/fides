# If you update this, also update `DEFAULT_PYTHON_VERSION` in the GitHub workflow files
ARG PYTHON_VERSION="3.10.11"
#########################
## Compile Python Deps ##
#########################
FROM python:${PYTHON_VERSION}-slim-bullseye as compile_image

# Install auxiliary software
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    g++ \
    gnupg \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python Dependencies
COPY dev-requirements.txt .
RUN pip install --user -U pip --no-cache-dir install -r dev-requirements.txt

COPY requirements.txt .
RUN pip install --user -U pip --no-cache-dir install -r requirements.txt

##################
## Backend Base ##
##################
FROM python:${PYTHON_VERSION}-slim-bullseye as backend

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Loads compiled requirements and adds the to the path
COPY --from=compile_image /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

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
COPY clients/package.json clients/package-lock.json ./
COPY clients/fides-js/package.json ./fides-js/package.json
COPY clients/admin-ui/package.json ./admin-ui/package.json
COPY clients/privacy-center/package.json ./privacy-center/package.json

RUN npm install

COPY clients/ .

####################
## Built frontend ##
####################
FROM frontend as built_frontend

# Builds and exports admin-ui
RUN npm run export-admin-ui
# Builds privacy-center
RUN npm run build-privacy-center

###############################
## Production Privacy Center ##
###############################
FROM node:16-alpine as prod_pc

WORKDIR /fides/clients

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs
USER nextjs

COPY --from=built_frontend --chown=nextjs:nodejs /fides/clients .
WORKDIR /fides/clients/privacy-center

EXPOSE 3000

CMD ["npm", "run", "start"]

############################
## Production Application ##
############################
FROM backend as prod

# Copy frontend build over
COPY --from=built_frontend /fides/clients/admin-ui/out/ /fides/src/fides/ui-build/static/admin

# Install without a symlink
RUN python setup.py sdist
RUN pip install dist/ethyca-fides-*.tar.gz

# Remove this directory to prevent issues with catch all
RUN rm -r /fides/src/fides/ui-build
