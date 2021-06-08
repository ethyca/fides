FROM python:3.9.5-alpine3.13

# Install requirements
RUN pip install mkdocs

# Copy in the files
COPY fides/ .

# Build the docs
RUN mkdocs build

EXPOSE 8000
ENTRYPOINT ["mkdocs"]
