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

Next, run `make server`. You can now visit [http://127.0.0.1:2000/](http://127.0.0.1:2000/) to explore the test app. It is a simple e-commerce 
marketplace where users can buy and sell products. 

Similarly you can visit [http://127.0.0.1:8080/docs](http://127.0.0.1:8080/docs) to check that fidesops is up and running and preview the set of API endpoints that are available for us to run requests on fidesops.