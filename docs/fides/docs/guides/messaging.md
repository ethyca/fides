# Configure Email/SMS Messaging
## What is email/SMS used for?

Fides supports email and SMS server configurations for sending processing notices to privacy request subjects. Future updates will support outbound email communications with data processors.

Supported modes of use:

- Subject Identity Verification - Used to verify subject identity before proceeding with their privacy request. For more information on identity verification in subject requests, see the [Privacy Requests](../getting-started/privacy_requests.md#subject-identity-verification) guide.
- Request Receipt Notification - Used to send subject notifications upon privacy request receipt.
- Request Review Notification - Used to send subject notifications upon privacy request review. Includes denial reason of the request, if applicable.
- Request Completion Notification - Used to send subject notifications upon privacy request completion. Includes link to download data package, if applicable.


## Prerequisites

Fides currently supports both Mailgun for email messaging and either Mailgun or Twilio fo SMS messaging.

For Mailgun, ensure you register or use an existing Mailgun account in order to get up and running with email communications.

1. Generate a Mailgun Domain Sending Key

    Follow the [Mailgun documentation](https://documentation.mailgun.com/en/latest/api-intro.html#authentication-1) to create a new Domain Sending Key for Fides. 

    !!! Note 
        Mailgun automatically generates a **primary account API key** when you sign up for an account. This key allows you to perform all CRUD operations via Mailgun's API endpoints, and for any of your sending domains. For security purposes, using a new **domain sending key** is recommended over your primary API key.

## Configuration

### Add necessary config variables

You'll need to set up config variables to send out messages from Fides. Refer to [the config variable reference](../installation/configuration.md#configuration-variable-reference) for more details.

Here's an example set of relevant configs to enable all notification types with a Mailgun service type.

```js
FIDES__EXECUTION__SUBJECT_IDENTITY_VERIFICATION_REQUIRED=true
FIDES__NOTIFICATIONS__NOTIFICATION_SERVICE_TYPE="mailgun"
FIDES__NOTIFICATIONS__SEND_REQUEST_COMPLETION_NOTIFICATION=true
FIDES__NOTIFICATIONS__SEND_REQUEST_RECEIPT_NOTIFICATION=true
FIDES__NOTIFICATIONS__SEND_REQUEST_REVIEW_NOTIFICATION=true
```

For the `FIDES__NOTIFICATIONS__NOTIFICATION_SERVICE_TYPE` variable, we currently support the following service types:

- `mailgun`
- `twilio_sms`
- `twilio_email`

These service types must correspond to the `service_type` in one of your messaging configs in the database.


### Create the messaging configuration

#### Mailgun Config

```json title="<code>POST api/v1/messaging/config"
{
    "key": "{{messaging_config_key}}",
    "name": "mailgun",
    "service_type": "mailgun",
    "details": {
        "domain": "your.mailgun.domain"
    }
}
```

#### Twilio SMS Config

```json title="<code>POST api/v1/messaging/config"
{
    "key": "{{twilio_config_key}}",
    "name": "twilio",
    "service_type": "twilio_text"
}
```

| Field          | Description                                                                                                                                                      |
|----------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `key`          | *Optional.* A unique key used to manage your messaging config. This is auto-generated from `name` if left blank. Accepted values are alphanumeric, `_`, and `.`. |
| `name`         | A unique user-friendly name for your messaging config.                                                                                                           |
| `service_type` | The email service to configure. Currently, Fides supports `mailgun`, `twilio_email`, and `twilio_sms`.                                                           |
| `details`      | A dict of key/val config vars specific to the messaging service.                                                                                                 |
| `domain`       | Your unique Mailgun domain.                                                                                                                                      |
| `is_eu_domain` | *Optional.* A boolean that denotes whether your Mailgun domain was created in the EU region. Defaults to `False`.                                                |
| `api_version`  | *Optional.* A string that denotes the API version. Defaults to `v3`.                                                                                             |


### Add the messaging configuration secrets 

#### Mailgun Secrets

```json title="<code>PUT api/v1/messaging/config/{{messaging_config_key}}/secret"
{
    "mailgun_api_key": "{{mailgun_api_key}}",
}

```

#### Twilio SMS Secrets

```json title="<code>PUT api/v1/messaging/config/{{messaging_config_key}}/secret"
{
    "twilio_account_sid": "{{twilio_account_sid}}",
    "twilio_auth_token": "{{twilio_auth_token}}",
    "twilio_messaging_service_sid": "{{twilio_messaging_service_id}}"
}

```

#### Twilio Email Secrets

```json title="<code>PUT api/v1/messaging/config/{{messaging_config_key}}/secret"
{
    "twilio_api_key": "{{twilio_api_key}}",
}

```

| Field                          | Description                                                                                                                |
|--------------------------------|----------------------------------------------------------------------------------------------------------------------------|
| `mailgun_api_key`              | Your Mailgun Domain Sending Key.                                                                                           |
| `twilio_account_sid`           | Your Twilio Account SID.                                                                                                   |
| `twilio_auth_token`            | Your Twilio Auth Token.                                                                                                    |
| `twilio_messaging_service_sid` | Your Twilio Messaging Service SID. One of `twilio_messaging_service_sid` or `twilio_sender_phone_number` must be provided. |
| `twilio_sender_phone_number`   | Your Twilio Sender Phone Number. One of `twilio_messaging_service_sid` or `twilio_sender_phone_number` must be provided.   |
| `twilio_api_key`               | Your Twilio API Key.                                                                                                       |

