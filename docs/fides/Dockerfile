FROM python:3.10.10-slim-bullseye as build

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    g++ \
    gnupg \
    gcc \
    python3-wheel \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY . .
RUN pip install -U pip && pip install . && pip install -r docs/fides/requirements.txt


FROM python:3.10.10-slim-bullseye as docs
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /docs

COPY --from=build /opt/venv /opt/venv
COPY --from=build /docs/fides .

ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8000
CMD ["mkdocs", "serve", "--dev-addr=0.0.0.0:8000"]
