FROM python:3.8-slim-buster

# Install auxiliary software
RUN apt-get update
RUN apt-get install -y \
    ipython \
    vim

# Update pip and install requirements
RUN pip install -U pip
COPY requirements.txt requirements.txt
COPY dev-requirements.txt dev-requirements.txt
COPY tests/.fides.conf.example .fides.conf
RUN pip install -r requirements.txt
RUN pip install -r dev-requirements.txt

# Copy in the application files and install it locally
COPY . /fidesctl
WORKDIR /fidesctl
RUN pip install -e .

CMD ["/bin/bash"]
