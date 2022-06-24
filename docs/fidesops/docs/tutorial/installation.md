# Installation

## Requirements 
To run this project, ensure you have the following requirements installed and running on your machine:

* [Docker 12+](https://docs.docker.com/desktop/#download-and-install)
* Python 3.8+
* Make
* pg_config (`brew install libpq` or `brew install postgres` on Mac)


## Clone the fidesdemo repo

Clone [Fides Demo](https://github.com/ethyca/fidesdemo), and run `make install` to begin setup. Among other things, this will create a [Flask](https://flask.palletsprojects.com/) app to mimic your application, and provide several YAML files that annotate the Flask app's databases. 
```bash
git clone https://github.com/ethyca/fidesdemo
cd fidesdemo
make install
source venv/bin/activate
```

You can run `make server` and visit [http://127.0.0.1:5000/](http://127.0.0.1:5000/) to explore the test app. It is a simple e-commerce 
marketplace where users can buy and sell products. 


## Install fidesops in our test app

We need to install fidesops in the test app, add a PostgreSQL database (for storing Fidesops resources)
and a Redis cache (for *temporarily* storing incoming PII). You'll notice that a postgres container has already been set 
up for you, and `fidesctl` is installed (although we won't dive into that tool here). In the Flask App's docker-compose file, 
add both a container for `redis` and `fidesops` services beneath the fidesctl `service`:


`fidesdemo/docker-compose.yml`:
```yaml
services:
  ...
  redis:
    image: "redis:6.2.5-alpine"
    command: redis-server --requirepass redispass
    expose:
      - 6379
    ports:
      - "6379:6379"

  fidesops:
    image: ethyca/fidesops:latest
    depends_on:
      - db
      - redis
    command: fidesops webserver
    volumes:
      - ./fides_uploads:/fidesops/fides_uploads
    expose:
      - 8000
    ports:
      - "8000:8080"
    environment:
      - FIDESOPS__SECURITY__APP_ENCRYPTION_KEY=QLMI5I0xLWUXE4JN4Asnba79JiBHWWM3
      - FIDESOPS__SECURITY__OAUTH_ROOT_CLIENT_ID=fidesopsadmin
      - FIDESOPS__SECURITY__OAUTH_ROOT_CLIENT_SECRET=fidesopsadminsecret
      - FIDESOPS__DATABASE__SERVER=db
      - FIDESOPS__DATABASE__USER=postgres
      - FIDESOPS__DATABASE__PASSWORD=postgres
      - FIDESOPS__DATABASE__DB=fidesops
      - FIDESOPS__DATABASE__PORT=5432
      - FIDESOPS__REDIS__HOST=redis
      - FIDESOPS__REDIS__PORT=6379
      - FIDESOPS__REDIS__PASSWORD=redispass
```

## Verify that fidesops is installed

Run `make_server` again:
```bash
  cd fidesdemo
  make server
```

Visit [http://localhost:8000/docs](http://localhost:8000/docs) to check that fidesops is up and running and preview the set of API endpoints 
that are available for us to run requests on fidesops.