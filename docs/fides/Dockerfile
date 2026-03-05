FROM python:3.13-slim-bookworm AS build

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    g++ \
    gnupg \
    gcc \
    git \
    python3-wheel \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install FreeTDS (used for PyMSSQL)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libssl-dev \
    libffi-dev \
    libkrb5-dev \
    unixodbc \
    unixodbc-dev \
    freetds-dev \
    freetds-bin \
    python-dev-is-python3 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Create venv and install with uv (reads [tool.uv.extra-build-dependencies] from pyproject.toml)
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY . .
# Pin setuptools so legacy deps (flatdict, scylla-driver) get pkg_resources in build isolation
RUN uv pip install --python /opt/venv/bin/python setuptools==80.10.2 wheel
RUN uv pip install --python /opt/venv/bin/python . && \
    uv pip install --python /opt/venv/bin/python -r docs/fides/requirements.txt


FROM python:3.13-slim-bookworm AS docs

# Add the fidesuser user
RUN addgroup --system --gid 1001 fidesgroup
RUN adduser --system --uid 1001 --home /home/fidesuser fidesuser

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy uv from build stage so runtime commands can use it (e.g. uv pip install -e /fides when repo is mounted)
COPY --from=build /root/.local/bin/uv /usr/local/bin/uv

WORKDIR /docs

COPY --from=build --chown=fidesuser:fidesgroup /opt/venv /opt/venv
COPY --from=build --chown=fidesuser:fidesgroup /docs/fides .

ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8000
CMD ["mkdocs", "serve", "--dev-addr=0.0.0.0:8000"]
