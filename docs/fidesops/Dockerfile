FROM python:3.8-slim-buster

# Install auxiliary software
RUN apt-get update
RUN apt-get install -y \
    git \
    vim

# Update pip and install requirements
RUN pip install -U pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy in the application files and install it locally
COPY ./docs /docs
WORKDIR /docs

EXPOSE 8000
CMD ["mkdocs", "serve", "--dev-addr=0.0.0.0:8000"]
