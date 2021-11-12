FROM python:3.8-slim-buster

# Install auxiliary software
RUN apt-get update
RUN apt-get install -y \
    git \
    ipython \
    make \
    vim \
    gcc

# libpq-dev provides all requirements for building Psycopg2
RUN apt-get -y install libpq-dev

# Update pip and install requirements
RUN pip install -U pip
COPY requirements.txt requirements.txt
COPY dev-requirements.txt dev-requirements.txt
RUN pip install -r requirements.txt
RUN pip install -r dev-requirements.txt

# Copy in the application files and install it locally
COPY . /fides/fidesctl
WORKDIR /fides/fidesctl
RUN pip install -e ".[all]"

# Immediately flush to stdout, globally
ENV PYTHONUNBUFFERED=TRUE

CMD ["/bin/bash"]
