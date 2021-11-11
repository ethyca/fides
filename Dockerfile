FROM python:3.9.6-slim-buster

# Install auxiliary software
RUN apt-get update && \
    apt-get install -y \
    git \
    make \
    ipython \
    vim \
    curl \
    gcc

# Update pip and install requirements
COPY requirements.txt dev-requirements.txt ./
RUN pip install -U pip && pip install -r requirements.txt -r dev-requirements.txt

# Copy in the application files and install it locally
COPY . /fidesops_install
WORKDIR /fidesops_install
RUN pip install -e .

WORKDIR /fidesops

CMD [ "fidesops", "webserver" ]