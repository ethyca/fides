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

# Copy in the required files
COPY ./docs /docs
WORKDIR /docs

# Generate the OpenAPI Docs
ADD generate_openapi.py generate_openapi.py
RUN python generate_openapi.py ./api/openapi.json


EXPOSE 8000
CMD ["mkdocs", "serve", "--dev-addr=0.0.0.0:8000"]
