# How-To: Execute Privacy Requests

In this section we'll cover:

- What is a Privacy Request?
- How does a Privacy Rquest work in conjunction with a policy?
- How can I execute a Privacy Request?
- How do I monitor Privacy Requests as they execute?
- How can I integrate the Privacy Request flow into my existing support tools?

Take me directly to [api docs](http://0.0.0.0:8080/docs#/Privacy%20Requests/create_privacy_request_api_v1_privacy_request_post).

## What is a Privacy Request?
A Privacy Request in its simplest form describes a request by a user, to process data pertaining to their identity. Privacy Requests are currently supported in two forms, `access` and `erasure`. For more information on action types, please see [How-To: Configure Request Policies](policies.md#rule-attributes).


#### How does a Privacy Request work in conjunction with a Policy?
A Privacy Request must always be associated with a pre-configured `Policy`. While a Privacy Request describes _whose_ data to process, a `Policy` describes _how_ to process that data.


## How can I execute a Privacy Request?
Privacy Requests can be executed by submitting them to Fidesops via the Privacy Request API as follows:

`POST /api/v1/privacy-request`

```
[
  {
    "external_id": "a-user-defined-id",
    "requested_at": "2021-10-31T16:00:00.000Z",
    "policy_key": "a-demo-policy",
    "identities": [{
      "email": "identity@example.com",
      "phone_number: "+1 (123) 456 7891"
    }],
  }
]
```

#### Note:

- This request will submit a Privacy Request for execution that applies the `a-demo-policy` Policy to all target data in the [Identity Graph](../glossary.md) that can be generated from the email address `identity@example.com` or the phone number `+1 (123) 456 7891`.
- Specifying a `external_id` enables us to track this Privacy Request with that `external_id` later on. See [How-To: Report on Privacy Requests](reporting.md) for more information.
- `policy_key` should correspond to a previously configured `Policy` object. See [How-To: Configure Request Policies](policies.md) for more information.
- A full list of attributes available to set on the Privacy Request can be found in the [api docs](/docs#/PrivacyRequest).


## How do I monitor Privacy Requests as they execute?
Privacy Requests can be monitored at any time throughout their execution by submitting any of the following requests:

`GET api/v1/privacy-request?id=<privacy_request_id>`

`GET api/v1/privacy-request?external_id=<external_id>`

For more detailed examples and further Privacy Request filtering in Fidesops please see [How-To: Report on Privacy Requests](reporting.md).


## How can I integrate the Privacy Request flow into my existing support tools?
Alongside generic API interopoerability, Fidesops provides a direct integration with the OneTrust's DSAR automation flow.

- Generic API interoperability: Third party services can be authorized by creating additional OAuth clients. Tokens obtained from OAuth clients can be managed and revoked at any time. Pleae see [How-To: Authenticate with OAuth](oauth.md) for more information.
- OneTrust: Fidesops can be configured to act as (or as part of) the fulfilment layer in OneTrust's Data Subject Request automation flow. Please see [How-To: Configure OneTrust Integration](onetrust.md) for more information.
