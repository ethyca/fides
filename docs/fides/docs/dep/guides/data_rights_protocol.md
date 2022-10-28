# Data Rights Protocol

The [Data Rights Protocol](https://github.com/consumer-reports-digital-lab/data-rights-protocol) (DRP) is a technical standard for exchanging data rights requests under regulations like the California Consumer Privacy Act (CCPA).

As a Privacy Infrastructure Provider (PIP), Fides conforms to the DRP standards to receive and process Data Rights Requests. The following endpoints and actions are available in Fides for working within the DRP specifications.

## DRP Actions

A [DRP action](https://github.com/consumer-reports-digital-lab/data-rights-protocol#301-supported-rights-actions) may be defined when creating or editing a [policy](policies.md#create-a-policy). These actions associate a Fides execution policy with a DRP-standardized protocol for receiving and processing Data Rights Requests.

A given action may only be associated to a single policy:

```yaml title="<code>PATCH /api/v1/policy</code>"
[
    {
        "name": "User Email Address",
        "key": "user_email_address_policy",
        "drp_action": "access"
    }
]
```

### Available actions

The following actions may be associated to a policy via the `drp_action` attribute, which correspond to the DRP's set of [supported rights](https://github.com/consumer-reports-digital-lab/data-rights-protocol#202-post-exercise-data-rights-exercise-endpoint).

| Action | Use |
|---|----|
| `sale:opt_out` | Right to opt out of data sale |
| `sale:opt_in` | Reconsent, or opt-in to data sale |
| `deletion` | Right to Delete |
| `access` | Right to Know |
| `access:categories` | Right to Know |
| `access:specific` | Right to Know |

## Endpoints

Once a policy is associated with an action, the following DRP-standardized endpoints are available.

### Exercise

The `/exercise` endpoint creates a new DRP privacy request. Fides will execute this request based on the policy associated to the DRP action specified in `exercise`.

All identity information should be encapsulated in the provided `identity` field using RFC7515-encoded [JSON Web Tokens](https://datatracker.ietf.org/doc/html/rfc7515). More about identity ecapsulation can be found in the [DRP standard](https://github.com/consumer-reports-digital-lab/data-rights-protocol#304-schema-identity-encapsulation).

```json title="<code>POST /api/v1/drp/exercise</code>"
{
  "meta": {
    "version": "0.5"
  },
  "exercise": [
    "sale:opt-out"
  ],
  "identity": "jwt",
}
```

```json title="Response"
{
    "request_id": "c789ff35-7644-4ceb-9981-4b35c264aac3",
    "received_at": "20210902T152725.403-0700",
    "expected_by": "20211015T152725.403-0700",
    "status": "open",
}
```

### Status

The current status of an existing privacy request may be returned via the `/status` endpoint, which must be queried using a privacy request ID.

```json title="<code>GET /api/v1/drp/status?request_id={privacy_request_id}</code>"
{
    "request_id": "c789ff35-7644-4ceb-9981-4b35c264aac3",
    "status": "open",
}
```

### Data Rights

All data rights associated with existing policies may be returned via the `/data-rights` endpoint. Note that the `v1` in the below URL does not correspond to DRP version, but instead corresponds to Fides version.

```json title="<code>GET /api/v1/drp/data-rights</code>"
{
    "version": "0.5",
    "api_base": null,
    "actions": [
        "access"
    ],
    "user_relationships": null
}
```

### Revoke

You can revoke a pending privacy request via the `/revoke` endpoint.

```json title="<code>GET /api/v1/drp/revoke</code>"
{
    "request_id": "c789ff35-7644-4ceb-9981-4b35c264aac3", 
    "reason": "Accidentally submitted"
}
```
