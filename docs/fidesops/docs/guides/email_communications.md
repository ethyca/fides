# Configure Automatic Emails
## What is a fidesops Email Connection?

Fidesops supports configuring third party email servers to handle outbound communications.

Supported modes of use:

- Subject Identity Verification - sends a verification code to the user's email address prior to processing a subject request. For more information on identity verification, see the [Privacy Requests](privacy_requests.md#subject-identity-verification) guide.
- Erasure Request Email Fulfillment - sends an email to configured third parties to process erasures for a given data subject.  See [creating email Connectors](#email-third-party-services) for more information.
- Privacy Request Receipt Notification - sends an email to user's email address with privacy request receipt notification.
- Privacy Request Review Notification - sends an email to user's email address upon privacy request review, including rejection reason if applicable.
- Privacy Request Completion Notification - sends an email to user's email address with privacy request completion notification, including a download link to data package, for access requests. For more information on request completion notification, see the [Privacy Requests](privacy_requests.md#request-completion-notification) guide.

## Prerequisites

Fidesops currently supports Mailgun for email integrations. Ensure you register or use an existing Mailgun account in order to get up and running with email communications.

1. Generate a Mailgun Domain Sending Key

    Follow the [Mailgun documentation](https://documentation.mailgun.com/en/latest/api-intro.html#authentication-1) to create a new Domain Sending Key for fidesops. 

!!! Note 
    Mailgun automatically generates a **primary account API key** when you sign up for an account. This key allows you to perform all CRUD operations via Mailgun's API endpoints, and for any of your sending domains. For security purposes, using a new **domain sending key** is recommended over your primary API key.

## Configuration

### Create the email config

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

```json title="<code>POST api/v1/email/config/{email_config_key}/secret"
{
    "mailgun_api_key": "nc123849ycnpq98fnu"
}

```

| Field | Description |
|---|----|
| `mailgun_api_key` | Your Mailgun Domain Sending Key. |

## Email third-party services

Once your email server is configured, you can create an email connector to send automatic erasure requests to third-party services. Fidesops will gather details about each collection described in the connector, and send a single email to the service after all collections have been visited. 

!!! Note
    Fidesops does not collect confirmation that the erasure was completed by the third party.


### Create the connector

Ensure you have created your [email configuration](#configuration) prior to creating a new email connector.

```json title="<code>PATCH api/v1/connection</code>"
[
  { 
    "name": "Email Connection Config",
    "key": "third_party_email_connector",
    "connection_type": "email",
    "access": "write"
  }
]
```

| Field | Description |
|----|----|
| `key` | A unique key used to manage your email connector. This is auto-generated from `name` if left blank. Accepted values are alphanumeric, `_`, and `.`. |
| `name` | A unique user-friendly name for your email connector. |
| `connection_type` | Must be `email` to create a new email connector. |
| `access` | Email connectors must be given `write` access in order to send an email. |


### Configure notifications

Once your email connector is created, configure any outbound email addresses:

```json title="<code>PUT api/v1/connection/{email_connection_config_key}/secret</code>" 
{
    "test_email": "my_email@example.com",
    "to_email": "third_party@example.com"
}
```

| Field | Description |
|----|----|
| `{email_connection_config_key}` | The unique key that represents the email connection to use. |
| `to_email` | The user that will be notified via email to complete an erasure request. *Only one `to_email` is supported at this time.* |
| `test_email` | *Optional.* An email to which you have access for verifying your setup. If your email configuration is working, you will receive an email with mock data similar to the one sent to third-party services. |

### Configure the dataset

Lastly, configure the collections and fields you would like to request be erased or masked. Fidesops will use these fields to compose an email to the third-party service. 

```json title="<code>PUT api/v1/connection/{email_connection_config_key}/dataset" 
[
    {
      "fides_key": "email_dataset",
      "name": "Dataset not accessible automatically",
      "description": "Third party data - will email to request erasure",
      "collections": [
        {
          "name": "daycare_customer",
          "fields": [
            {
              "name": "id",
              "data_categories": [
                "system.operations"
              ],
              "fidesops_meta": {
                "primary_key": true
              }
            },
            {
              "name": "child_health_concerns",
              "data_categories": [
                "user.biometric_health"
              ]
            },
            {
              "name": "user_email",
              "data_categories": [
                "user.contact.email"
              ],
              "fidesops_meta": {
                "identity": "email"
              }
            }
          ]
        }
      ]
    }
]
```

| Field | Description |
|----|----|
| `fides_key` | A unique key used to manage your email dataset. This is auto-generated from `name` if left blank. Accepted values are alphanumeric, `_`, and `.`. |
| `name` | A unique user-friendly name for your email dataset. |
| `description` | Any additional information used to describe this email dataset. |
| `collections` | Any collections and associated fields belonging to the third party service, similar to a configured fidesops [Dataset](datasets.md). If you do not know the exact data structure of a third party's database, you can configure a single collection with the fields you would like masked. **Note:** A primary key must be specified on each collection. |