# Configure Email Communications
## What is email used for?

Fidesops supports email server configurations for sending processing notices to privacy request subjects. Future updates will support outbound email communications with data processors.

Supported modes of use:

- Subject Identity Verification - for more information on identity verification in subject requests, see the [Privacy Requests](privacy_requests.md#subject-identity-verification) guide.


## Prerequisites

Fidesops currently supports Mailgun for email integrations. Ensure you register or use an existing Mailgun account in order to get up and running with email communications.

1. Generate a Mailgun Domain Sending Key

    Follow the [Mailgun documentation](https://documentation.mailgun.com/en/latest/api-intro.html#authentication-1) to create a new Domain Sending Key for fidesops. 

    !!! Note 
        Mailgun automatically generates a **primary account API key** when you sign up for an account. This key allows you to perform all CRUD operations via Mailgun's API endpoints, and for any of your sending domains. For security purposes, using a new **domain sending key** is recommended over your primary API key.

## Configuration

### Create the email configuration

```json title="<code>POST api/v1/email/config"
{
    "key": "{{email_config_key}}",
    "name": "mailgun",
    "service_type": "mailgun",
    "details": {
        "domain": "your.mailgun.domain"
    }
}
```

| Field | Description |
|----|----|
| `key` | *Optional.* A unique key used to manage your email config. This is auto-generated from `name` if left blank. Accepted values are alphanumeric, `_`, and `.`. |
| `name` | A unique user-friendly name for your email config. |
| `service_type` | The email service to configure. Currently, fidesops supports `mailgun`. |
| `details` | A dict of key/val config vars specific to Mailgun. |
| `domain` | Your unique Mailgun domain. |
| `is_eu_domain` | *Optional.* A boolean that denotes whether your Mailgun domain was created in the EU region. Defaults to `False`. |
| `api_version` | *Optional.* A string that denotes the API version. Defaults to `v3`. |


### Add the email configuration secrets 

```json title="<code>POST api/v1/email/config/{{email_config_key}}/secret"
{
    "mailgun_api_key": "nc123849ycnpq98fnu"
}

```

| Field | Description |
|---|----|
| `mailgun_api_key` | Your Mailgun Domain Sending Key. |

