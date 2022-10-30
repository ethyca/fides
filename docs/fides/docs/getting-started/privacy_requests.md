# Execute Privacy Requests
## What is a Privacy Request?

A privacy request represents an ask from a user to perform an action on their identity data. The request itself identifies the user by email address, phone number, social security number, or other identifiable information. The data that will be affected, and how it's affected, is described in an execution policy associated with the request.

For more information on policies, see the [execution policies](./execution_policies.md#rule-attributes) guide.

## Submit a privacy request

!!! Tip "Privacy Requests are executed immediately by default. This setting may be changed in your `fides.toml` configuration file."

Privacy requests are submitted by calling the [Privacy Request](../api/index.md#operations-tag-Privacy_Requests) endpoint:

```json title="<code>POST /api/v1/privacy-request</code>"
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

The above request will apply the `a-demo-policy` execution policy to all target data that can be generated from the email address `identity@example.com`, and the phone number `+1 (123) 456 7891`. 

| Attribute | Description |
|---|---|
| `external_id` | *Optional.* An identifier that lets you track the privacy request. See [Report on Privacy Requests](../guides/reporting.md) for more information. |
| `requested_at` | *Optional.* An ISO8601 timestamp that specifies the moment that the request was submitted. Defaults to the `created_at` time if not specified. |
| `policy_key` | Identifies the [execution policy](./execution_policies.md) applied to this request. |
| `identities` | An array of objects. These objects identify any users whose data will be affected by the execution policy. Each object identifies a single user.  |

A full list of attributes available to set on a privacy request can be found in the [API documentation](../api/index.md#operations-tag-Privacy_Requests).


### Enable subject identity verification 
Verifying user identity prior to processing their privacy request requires the following:

1. Set the `subject_identity_verification_required` variable in your `fides.toml` to `TRUE`. 
2. [Configure Emails](../guides/email_communications.md) that lets Fides send automated emails to your users.

With identify verification enabled, a user will be emailed a six-digit code when they submit a privacy request. They must supply that verification code to Fides to continue privacy request execution.  

Until the Privacy Request identity is verified, it will have a status of `identity_unverified`:

```json title="<code>POST api/v1/privacy-request/<privacy_request_id>/verify</code>"
{"code": "<verification code here>"}
```

## Privacy request actions
### Approve and deny privacy requests

 Fides processes privacy requests immediately by default. To review privacy requests before they are executed, the `require_manual_request_approval` variable in your `fides.toml` must be set to `TRUE`.

To process pending privacy requests, a list of privacy request IDs must be sent to the `approve` or `deny` endpoints. Both endpoints support processing requests in bulk.

```json title="<code>PATCH api/v1/privacy-request/administrate/approve</code>"
{
  "request_ids":[
    "pri_2d181f15-486d-4bcf-a871-f50ed9f95673",
    "pri_2d181f15-486d-4bcf-a871-f50ed9f95673"
  ]
}
```

An optional denial reason can be provided when denying a privacy request:
```json title="<code>PATCH api/v1/privacy-request/administrate/deny</code>"
{
  "request_ids":[
    "pri_2d181f15-486d-4bcf-a871-f50ed9f95673",
    "pri_2d181f15-486d-4bcf-a871-f50ed9f95673"
  ],
  "reason": "Requests denied because they're duplicates"
}
```

### Monitor ongoing requests
Privacy requests can be monitored at any time throughout their execution by calling either of the following endpoints:

```
GET api/v1/privacy-request?request_id=<privacy_request_id>
```

```
GET api/v1/privacy-request?external_id=<external_id>
```

For more detailed examples and further privacy request filtering, see [Reporting on Privacy Requests](../guides/reporting.md).

### Restart failed requests
To restart a failed privacy request, call the following endpoint with an empty request body:

```
POST /api/v1/privacy-request/<privacy_request_id>/retry
```

## Encrypt your requests
Access request results can be optionally encrypted by supplying an `encryption_key` string in the request body. Fides uses the supplied `encryption_key` to encrypt the contents of your JSON and CSV results using an AES-256 algorithm in GCM mode.

When converted to bytes, your `encryption_key` must be 16 bytes long. The data returned will have the nonce concatenated 
to the encrypted data.

```json title="<code>POST /privacy-request</code>"
[
    {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "identity": {"email": "customer-1@example.com"},
        "policy_key": "my_access_policy",
        "encryption_key": "test--encryption"
    }
]

```

### Decrypt your results

If you specified an encryption key, Fides encrypted the result data using your key and an internally-generated `nonce` with an AES 256 algorithm in GCM mode. The return value is a 12-byte nonce plus the encrypted data that is b64 encoded together.

```
+------------------+-------------------+
| nonce (12 bytes) | message (N bytes) |
+------------------+-------------------+
```

For example, if you specified an encryption key of `test--encryption`, and resulting data was uploaded to
S3 in a JSON file `GPUiK9tq5k/HfBnSN+J+OvLXZ+GCisapdI2KGP7A1WK+dz1XHef+hWb/SjszdqdNVGvziyY6GF5KIrvrXgxjZuaAvgU='`, you would
need to implement something similar to the snippet below to decrypt the result:

```python title="Sample decryption"
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

```python title="Sample result"
>>> {"street": "test street", "state": "NY"}
```

If CSV data was uploaded, each CSV in the zipfile was encrypted using a different nonce, so you'll need to follow
a similar process for each CSV file.

## Privacy request integrations

* **Generic API interoperability**: Third party services can be authorized by creating additional OAuth clients. Tokens obtained from OAuth clients can be managed and revoked at any time. See [authenticating with OAuth](../guides/oauth.md) for more information.