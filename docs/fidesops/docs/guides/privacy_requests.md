# How-To: Execute Privacy Requests

In this section we'll cover:


- What is a Privacy Request?
- How does a Privacy Request work in conjunction with a policy?
- How can I submit a Privacy Request?
- How can I approve/deny a Privacy Request? 
- How do I monitor Privacy Requests as they execute?
- How can I integrate the Privacy Request flow into my existing support tools?
- Specifying encryption of access request results 
- Decrypting access request results

Take me directly to [API docs](/fidesops/api#operations-Privacy_Requests-get_request_status_api_v1_privacy_request_get).

## What is a Privacy Request?

A Privacy Request represents a request to perform an action on a user's identity data. The Request object itself identifies the user by email address, phone number, social security number, or other identifiable information. The data that will be affected and how it's affected is described in a Policy object that's associated with the Request.

For more information on Policies, see [How-To: Configure Policies](policies.md#rule-attributes).


## How do I submit a Privacy Request?

You submit a Privacy Request by calling the  **Submit a Privacy Request** operation. Here, 
we submit  a request to apply the `a-demo-policy` Policy to all target data in the [Identity Graph](../glossary.md) that can be generated from the email address `identity@example.com` and the phone number `+1 (123) 456 7891`.
Privacy Requests are executed immediately by default. This setting may be changed in the fidesops.toml configuration file.

`POST /api/v1/privacy-request`

```json
[
  {
    "external_id": "a-user-defined-id",
    "requested_at": "2021-10-31T16:00:00.000Z",
    "policy_key": "a-demo-policy",
    "identity": {
      "email": "identity@example.com",
      "phone_number": "+1 (123) 456 7891"
    }
  }
]
```

* `external_id` is an optional  identifier of your own invention that lets you track the Privacy Request. See [How-To: Report on Privacy Requests](reporting.md) for more information.

* `requested_at` (Optional) is an ISO8601 timestamp that specifies the moment that the request was submitted. Defaults to the `created_at` time if not specified.

* `policy_key` identifies the Policy object to which this request will be applied. See [How-To: Configure Request Policies](policies.md) for more information.

* `identities` is an array of objects that contain data that identify the users whose data will be affected by the Policy. Each object identifies a single user by AND'ing the object's properties. 


- This request will submit a Privacy Request for execution that applies the `a-demo-policy` Policy to all target data in the [Identity Graph](../glossary.md) that can be generated from the email address `identity@example.com` or the phone number `+1 (123) 456 7891`.
- Specifying a `external_id` enables us to track this Privacy Request with that `external_id` later on. See [How-To: Report on Privacy Requests](reporting.md) for more information.
- `policy_key` should correspond to a previously configured `Policy` object. See [How-To: Configure Request Policies](policies.md) for more information.

A full list of attributes available to set on the Privacy Request can be found in the [API docs](/fidesops/api#operations-Privacy_Requests-get_request_status_api_v1_privacy_request_get).


## How can I approve or deny a Privacy Request?

Privacy Requests are executed immediately by default. To review Privacy Requests before they are executed, set the `REQUIRE_MANUAL_REQUEST_APPROVAL` variable in your `fidesops.toml` to `TRUE`.

To process Privacy Requests, send a list of Privacy Request IDs to the `approve` or `deny` endpoints. Both endpoints support processing requests in bulk.

```json title="<code>PATCH api/v1/privacy-request/administrate/approve</code>"
{
  "request_ids":[
    "pri_2d181f15-486d-4bcf-a871-f50ed9f95673",
    "pri_2d181f15-486d-4bcf-a871-f50ed9f95673"
  ]
}
```

An optional denial reason can be provided when denying a Privacy Request:

```json title="<code>PATCH api/v1/privacy-request/administrate/deny</code>"
{
  "request_ids":[
    "pri_2d181f15-486d-4bcf-a871-f50ed9f95673",
    "pri_2d181f15-486d-4bcf-a871-f50ed9f95673"
  ],
  "reason": "Requests denied because they're duplicates"
}
```

## How do I monitor Privacy Requests as they execute?
Privacy Requests can be monitored at any time throughout their execution by submitting any of the following requests:

`GET api/v1/privacy-request?request_id=<privacy_request_id>`

`GET api/v1/privacy-request?external_id=<external_id>`

For more detailed examples and further Privacy Request filtering in Fidesops please see [How-To: Report on Privacy Requests](reporting.md).


## How can I integrate the Privacy Request flow into my existing support tools?

Alongside generic API interoperability, Fidesops provides a direct integration with the OneTrust's DSAR automation flow.

* Generic API interoperability: Third party services can be authorized by creating additional OAuth clients. Tokens obtained from OAuth clients can be managed and revoked at any time. See [How-To: Authenticate with OAuth](oauth.md) for more information.

* OneTrust: Fidesops can be configured to act as (or as part of) the fulfillment layer in OneTrust's Data Subject Request automation flow. Please see [How-To: Configure OneTrust Integration](onetrust.md) for more information.

- Generic API interoperability: Third party services can be authorized by creating additional OAuth clients. Tokens obtained from OAuth clients can be managed and revoked at any time. Please see [How-To: Authenticate with OAuth](oauth.md) for more information.
- OneTrust: Fidesops can be configured to act as (or as part of) the fulfilment layer in OneTrust's Data Subject Request automation flow. Please see [How-To: Configure OneTrust Integration](onetrust.md) for more information.


## Encryption

You can optionally encrypt your access request results by supplying an `encryption_key` string in the request body:
We will use the supplied encryption_key to encrypt the contents of your JSON and CSV results using an AES-256 algorithm in GCM mode.
When converted to bytes, your encryption_key must be 16 bytes long.  The data we return will have the nonce concatenated 
to the encrypted data.

POST /privacy-request
```json
[
    {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "identity": {"email": "customer-1@example.com"},
        "policy_key": "my_access_policy",
        "encryption_key": "test--encryption"
    }
]

```

## Decrypting your access request results

If you specified an encryption key, we encrypted the access result data using your key and an internally-generated `nonce` with an AES 
256 algorithm in GCM mode.  The return value is a 12-byte nonce plus the encrypted data that is all b64encoded together.

```
+------------------+-------------------+
| nonce (12 bytes) | message (N bytes) |
+------------------+-------------------+
```

For example, pretend you specified an encryption key of `test--encryption`, and the resulting data was uploaded to
S3 in a JSON file: `GPUiK9tq5k/HfBnSN+J+OvLXZ+GCisapdI2KGP7A1WK+dz1XHef+hWb/SjszdqdNVGvziyY6GF5KIrvrXgxjZuaAvgU='`.  You will
need to implement something similar to the snippet below on your end to decrypt:

```python
import json
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

encrypted: str = "GPUiK9tq5k/HfBnSN+J+OvLXZ+GCisapdI2KGP7A1WK+dz1XHef+hWb/SjszdqdNVGvziyY6GF5KIrvrXgxjZuaAvgU=" 
encryption_key: str = "test--encryption".encode("utf-8")  # Only you know this

encrypted_combined: bytes = base64.b64decode(encrypted)
nonce: bytes = encrypted_combined[0:12]
encrypted_message: bytes = encrypted_combined[12:]
gcm = AESGCM(encryption_key)

decrypted_bytes: bytes = gcm.decrypt(nonce, encrypted_message, nonce)
decrypted_str: str = decrypted_bytes.decode("utf-8")

json.loads(decrypted_str)
```

```python
>>> {"street": "test street", "state": "NY"}
```

If CSV data was uploaded, each CSV in the zipfile was encrypted using a different nonce, so you'll need to follow
a similar process for each csv file.