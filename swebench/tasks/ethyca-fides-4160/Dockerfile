FROM python:3.10

RUN apt-get update && apt-get install -y \
    git curl ca-certificates patch build-essential \
    libpq-dev postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools wheel

WORKDIR /workspace

RUN git clone https://github.com/ethyca/fides.git /workspace/repo && cd /workspace/repo && \
    BASE=ddbae008c9fa37065141be475f3cd3a30a4fc5bc && \
    cur_branch="$(git rev-parse --abbrev-ref HEAD)" && \
    git reset --hard "$BASE" && \
    git for-each-ref --format='%(refname:short)' refs/heads | while read -r b; do \
      [ "$b" = "$cur_branch" ] || git branch -D "$b"; \
    done && \
    git remote | xargs -r -n1 git remote remove && \
    rm -f .git/config.lock && \
    git reflog expire --expire=now --all && \
    git gc --prune=now --aggressive

WORKDIR /workspace/repo

RUN pip install snowflake-connector-python==3.6.0

RUN pip install -r requirements.txt

RUN pip install -r dev-requirements.txt

RUN pip install -e .

ENV PYTHONPATH=/workspace/repo/src:$PYTHONPATH
ENV FIDES__TEST_MODE=true

WORKDIR /workspace
