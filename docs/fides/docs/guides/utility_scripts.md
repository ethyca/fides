# Configuring Fides via utility functions

Fides is a complex product, and accurate configuration can be hard. Rather than using the built-in Fides postman collection, you may find it faster to build configuration scripts in Python, using the primitives provided in the `scripts/setup/` directory.

## Available functions

The available functions are listed below:

| Function |
|----------|
| `setup.authentication.get_auth_header` |
| `setup.healthcheck.check_health` |
| `setup.s3_storage.create_s3_storage` |
| `setup.policy.create_policy` |
| `setup.rule.create_rule` |
| `setup.rule_target.create_rule_target` |
| `setup.email.create_email_integration` |
| `setup.rule.create_rule_target` |
| `setup.postgres_connector.create_postgres_connector` |
| `setup.mongodb_connector.create_mongodb_connector` |
| `setup.privacy_request.create_privacy_request` |
| `setup.subject_identity_verification.verify_subject_identity` |

Each script uses the Fides API to create its corresponding primitive object in Fides config.

## Secrets management

Some third party integrations require secrets to grant access. Custom scripts are configured to read these secrets as constant variables from a `scripts/setup/secrets.py` file. Due to its sensitive nature, this file is not supplied in the repository, and should be created in the format:

```python
AWS_ACCESS_KEY_ID = ""
AWS_ACCESS_SECRET_ID = ""

MAILCHIMP_SECRETS = {
    "domain": "",
    "username": "",
    "api_key": "",
}

MAILGUN_API_KEY = ""
```

## Writing custom scripts

Custom scripts can be written in the style of `scripts/setup/example_script.py`, where each method is called and given the requisite `auth_header` obtained from the `get_auth_header` primitive. Custom scripts should live in the `scripts/` directory in the root to ensure they are runnable with the nox command detailed below.

## Invoking custom scripts

Custom scripts can be invoked using the `run_script` nox command, and passing the script name as an argument. For example: `nox -s run_script -- example_script` will run the example script.

Please note that custom scripts will not run the Fides webserver, and should be invoked _after_ the `nox -s dev` command (or similar) has been run.
