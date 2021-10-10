# Fidesctl CLI

---

The Fidesctl CLI wraps the entire functionality of Fidesctl into a few succint commands.

## Commands

This is a non-exhaustive list of available Fidesctl CLI commands:

* `fidesctl apply [OPTIONS] MANIFESTS_DIR` 
   - Creates or Updates resources found within the YAML file(s) at the specified path. It sends the manifest files to the server. 
   - Options:
     * --dry: runs the command without any side effects
     * --diff: outputs a detailed diff of the local resource 
* `fidesctl evaluate [OPTIONS] MANIFESTS_DIR` 
   - Runs an evaluation of all policies, but a single policy can be specified using the `--fides-key` parameter.
   - Options:
     * -k, --fides-key TEXT: the fides_key for the specific Policy to be evaluated
     * -m, --message TEXT: description of the changes this evaluation encapsulates 

     * --dry: runs the command without any side effects 
* `fidesctl init-db` 
   - Sets up the database by running all missing migrations. It builds the required images, spins up the database, and runs the initalization script as you can see below. 
    ```ruby
      ~/git/fides% fidesctl init-db
      INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
      INFO  [alembic.runtime.migration] Will assume transactional DDL.
    ```
* `fidesctl get <resource_type> <fides_key>` 
  - Looks up a specific resource on the server by its type and `fides_key`.
  - `resource_type` options:
    * data_category
    * data_qualifier
    * data_subject
    * data_use
    * dataset
    * organization
    * policy
    * registry
    * system
* `fidesctl ls <resource_type>` 
  - Shows a list of all resources of a certain type that exist on the server.
  - `resource_type` options:
     * data_category
     * data_qualifier
     * data_subject
     * data_use
     * dataset
     * organization
     * policy
     * registry
     * system
* `fidesctl ping` 
  - Pings the API's health check endpoint to make sure that it is reachable and ready for requests. You should see the following response for this comand: 
   ```ruby
   Pinging http://fidesctl:8080/health...
   {
    "data": {
     "message": "Fides service is healthy!"
    }
   }
   ```
* `fidesctl reset-db` 
   - Tears down the database, erasing all data and re-initalizes the database. 
  ```ruby
   root@8caf03deae24:/fides/fidesctl# fidesctl reset-db
   This will drop all data from the Fides database!
   Are you sure [y/n]?
  ```
* `fidesctl --version` - Shows the version of Fides that is installed.
  ```ruby
  root@90ad65c0975c:/fides/fidesctl# fidesctl --version
  fidesctl, version 0.9.8.2+10.g1f86b00
  ```
* `fidesctl view-config`- Show a JSON representation of the config that Fidesctl is using.
  ```ruby
  {
    "api": {
      "database_url": "postgresql+psycopg2://fidesctl:fidesctl@fidesctl-db:5432/fidesctl"
    },
    "cli": {
      "server_url": "http://fidesctl:8080"
    },
    "user": {
      "user_id": "1",
      "api_key": "test_api_key",
      "request_headers": {
        "Content-Type": "application/json",
        "user-id": "1",
        "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1aWQiOjF9.uZEytEk5nO7uxQgmk9mN0zND3qfM1Bl3mNp_GyYsiVE"
      }
    }
  }
  ```
