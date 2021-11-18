# Tutorial Overview

In this tutorial you will learn how to use fidesctl to solve a real-world data privacy problem. These steps closely follow the example found in the `ethyca/fidesdemo` repository [here](https://github.com/ethyca/fidesdemo).

You will run a local instance of a basic web app to demonstrate the use of Fidesctl as part of a "real" project that uses:

* Flask to run a web server simulating a basic e-commerce application
* PostgreSQL as the application's database
* SQLAlchemy to connect to the database
* [`fidesctl`](https://github.com/ethyca/fides) to declare privacy manifests and evaluate policies

The app itself is the [Flask tutorial app](https://flask.palletsprojects.com/en/2.0.x/tutorial/), but modified to simulate an e-commerce marketplace. This helps to highlight some basic examples of data categories that might be stored in a "real" user-facing application.

## Setup Instructions

### System Requirements

Before beginning, ensure you have the following software installed and configured to your liking:

* Docker (v12+)
* Python (v3.7+)
* Make
* `pg_config` (required for the Python project. Installed via Homebrew with `brew install libpq` or `brew install postgres`.)

### Installation

1. Clone [the `ethyca/fidesdemo` repository](https://github.com/ethyca/fidesdemo) to your machine.
1. Checkout the repository's [`tutorial-start` tag](https://github.com/ethyca/fidesdemo/releases/tag/tutorial-start):

    ```shell
    git checkout tutorial-start
    ```

    Each step in this tutorial will explain the changes made in each commit of the fidesdemo repository. You can follow along by checking out each one, or by building everything yourself and comparing your work to each commit's changeset.

1. Navigate to the repository directory in your command line, and run:

    ```shell
    make install
    ```

    This will create the project's virtual environment, and set up all required containers, databases, and dependencies.

    If you prefer, you may execute the project's test suite by running:

    ```shell
    make test
    ```

## About the Example Application ("Flaskr")

This example application is meant to simulate a basic e-commerce marketplace where users can create accounts and purchase products from one another. Using the web app you can:

* Register a new user
* Login as a user
* Post a "product" for sale
* Delete/update products you've posted
* Purchase a product (no products are actually for sale)

The schema itself is designed to highlight a few *very* simple examples of how identifiable data might get stored in a web application like this one. The sample data below shows what this looks like:

```shell
flaskr=# SELECT * FROM users;
 id |     created_at      |       email       |              password              | first_name | last_name
----+---------------------+-------------------+------------------------------------+------------+-----------
  1 | 2020-01-01 00:00:00 | admin@example.com | pbkdf2:sha256:260000$O87nanbSkl... | Admin      | User
  2 | 2020-01-03 00:00:00 | user@example.com  | pbkdf2:sha256:260000$PGcBy5NzZe... | Example    | User
(2 rows)

flaskr=# SELECT * FROM products;
 id |     created_at      | seller_id |       name        |             description              | price
----+---------------------+-----------+-------------------+--------------------------------------+-------
  1 | 2020-01-01 12:00:00 |         1 | Example Product 1 | A description for example product #1 |    10
  2 | 2020-01-02 12:00:00 |         1 | Example Product 2 | A description for example product #2 |    20
  3 | 2020-01-03 12:00:00 |         2 | Example Product 3 | A description for example product #3 |    50
(3 rows)

flaskr=# SELECT * FROM purchases;
 id |     created_at      | product_id | buyer_id |    street_1    | street_2 |    city     | state |  zip
----+---------------------+------------+----------+----------------+----------+-------------+-------+-------
  1 | 2020-01-04 12:00:00 |          1 |        2 | 123 Example St | Apt 123  | Exampletown | NY    | 12345
(1 row)
```

## Check Your Progress

After running the commands outlined in the [Installation](#installation) section, your app should resemble the state of the [`ethyca/fidesdemo` repository](https://github.com/ethyca/fidesdemo) at the [`tutorial-start`](https://github.com/ethyca/fidesdemo/releases/tag/tutorial-start) tag.

## Next: Add Fidesctl to the App

Work within the sample app prior to the installation and configuration of the Fides developer tools to [add fidesctl](add.md).
