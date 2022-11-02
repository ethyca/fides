# Configure Policies
## What is an execution policy?

An execution policy (separate from a [Policy](../guides/policies.md), used to enforce compliance) is a set of instructions, or Rules, that are executed when a user submits a [request](./privacy_requests.md) to retrieve or delete their data. It describes how to access, mask, or erase data that matches specific data categories in submitted privacy requests.

Each endpoint takes an array of objects to create multiple policies, rules, or targets at one time.

!!! Tip "Regarding `PATCH` endpoints"
    `PATCH` requests perform the equivalent of a `create_or_update` operation. This means that any existing objects sent to this endpoint will:

    - be updated,
    - any non-existing objects will be created, AND
    - any objects existing that are not specified in the request will not be deleted.

## Create a Policy

To create a new execution policy, it must first be defined:

```json title="<code>PATCH /api/v1/policy</code>"
[
  {
    "name": "User Email Address",
    "key": "user_email_address_policy",
    "drp_action": "access", // optional
    "execution_timeframe": 7

  }
]
```
### Policy attributes
| Attribute | Description |
|---|---|
| `name` | User-friendly name for your Policy. |
| `key` | Unique key by which to reference the Policy. |
| `drp_action` | *Optional.* A [Data Rights Protocol](../guides/data_rights_protocol.md) action to associate to this policy. Accepted values are `access` (must be used with an [access Rule](#add-a-rule)) or `deletion` (must be used with an [erasure Rule](#add-an-erasure-rule)). |
| `execution_timeframe` | The time in which to fulfill an associated privacy request, in days. |

## Add a Rule
The policy creation operation returns an execution policy key. This key can be used to add a Rule to the execution policy. Rules represent a series of information and actions to take when a privacy request of the corresponding `action_type` is submitted.

The following is an example of an access Rule:

```json title="<code>PATCH /api/v1/policy/{policy_key}/rule</code>"
[
  {
    "name": "Access User Email Address",
    "key": "access_user_email_address_rule",
    "action_type": "access",
    "storage_destination_key": "storage_key"
  }
]
```
### Rule attributes
| Attribute | Description |
|---|---|
| `name` | A user-friendly name for the rule.
| `action_type` | Which action is this `Rule` handling?
| `action_type.access` | A data subject access request. Matching data will be returned.
| `action_type.erasure` | A data subject erasure request (or Right to be Forgotten). Matching data will be erased or [masked](../guides/masking_strategies.md).
| `storage_destination` | Where Fides will upload the returned data for an `access` action. See [storage](./storage.md). |
| `masking_strategy` | How to erase data that applies to this `Rule`. See [Configuring Masking Strategies](../guides/masking_strategies.md) |

!!! Note "The `storage_key` must identify an existing [Storage](./storage.md) object."

### Add a Rule Target
A Rule also specifies one or more [Data Categories](https://ethyca.github.io/fideslang/taxonomy/data_categories/), or "Targets", to which the rule applies. Creating a Rule will return a key, which can be used to assign it one or more targets:

```json title="<code>PATCH /api/v1/policy/{policy_key}/rule/{rule_key}/target</code>"
[
  {
    "name": "Access User Email Address Target",
    "key": "access_user_email_address_target",
    "data_category": "user.contact.email",
  }
]
```

| Attribute | Description |
|---|---|
| `name` | A user-friendly name for the target.
| `key` | A unique key to identify the target.
| `data_category` | The data categories to which the associated rule applies. For example, email addresses under `user.contact.email`. |

### Add an erasure Rule
!!! Tip "Access rules will always run before erasure rules."

The access execution policy created above will pull all data of category `user.contact.email`. In the event of an erasure request, we might also want to mask this information. 

A new `erasure` rule can be added to the same execution policy: 

```json title="<code>PATCH /api/v1/policy/{policy_key}/rule</code>"
[
  {
    "name": "Mask Provided Emails",
    "key": "mask_provided_emails",
    "action_type": "erasure",
    "masking_strategy": {
      "strategy": "hash",
      "configuration": {
        "algorithm": "SHA-512"
      },
    },
  },
]
```
This will create a Rule to hash an unspecified value with a SHA-512 hash. To add a value to hash, create a new Target for this Rule:

```json title="<code>PATCH api/v1/policy/{policy_key}/rule/{rule_key}</code>"
  [
    {
      "data_category": "user.contact.email",
    },
  ]
```

This execution policy, `user_email_address_policy`, will now do the following:
- Return all data with a data category that matches (or is nested under) `user.contact`.
- Mask all data with data category that matches `user.contact.email` with a the `SHA-512` hashing function.

#### Erasing data
When an execution policy Rule erases data, it erases the _entire_ branch given by the Target. For example, a `user.contact` Rule, will erase _all_ of the information within the `contact` node, including `user.contact.email`.

It's illegal to erase the same data twice within an execution policy. For example, erasing `user.contact` _and_ `user.contact.email` is not allowed.

## Default execution policies
!!! Tip "These auto-generated execution policies are intended for use in a test environment. In production deployments, configure separate execution policies and storage destinations that target and process the appropriate fields."

Fides ships with two default execution policies: `download` (for access requests) and `delete` (for erasure requests).  

* The `download` execution policy is configured to retrieve `user` data and upload to a local storage location.
* The `delete` execution policy is set up to mask `user` data with the string "`MASKED`".  