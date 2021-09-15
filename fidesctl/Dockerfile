FROM python:3.8-slim-buster

# Install auxiliary software
RUN apt-get update \
    && apt-get -y install libpq-dev gcc
    
RUN apt-get install -y \
    git \
    ipython \
    make \
    vim

# Update pip and install requirements
RUN pip install -U pip
COPY requirements.txt requirements.txt
COPY dev-requirements.txt dev-requirements.txt
RUN pip install -r requirements.txt
RUN pip install -r dev-requirements.txt

# Copy in the application files and install it locally
COPY . /fides/fidesctl
WORKDIR /fides/fidesctl
RUN pip install -e .

CMD ["/bin/bash"]
