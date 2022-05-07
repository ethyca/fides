# How-To: Configure Policies


A Policy is a set of instructions (or "Rules") that are executed when a user submits a request to retrieve or delete their data (the user makes a "Privacy Request"). Each Rule contains an "execution strategy":

* `action_type`: The action this Rule performs, either `access` (retrieve data) or `erasure` (delete data).

* `storage_destination`: If the `action_type` is `access`, this is the key of a `StorageConfig` object that defines where the data is uploaded.  Currently, Amazon S3 buckets and local filesystem storage are supported. See [How-To: Configure Storage](storage.md) for more information.

* `masking_strategy`: If the `action_type` is `erasure`, this is the key of a Masking object that defines how the erasure is implemented. See [How-To: Configure Masking Strategies](masking_strategies.md) for a list of masking strategies. 

In addition to specifying an execution strategy, a Rule contains one or more Data Categories, or "Targets", to which the rule applies. Putting it all together, we have:
```
Policy
  |-> Rules
      |-> Targets
```

This is reflected in the API paths that create these elements:

* `PATCH /policy`
* `PATCH /policy/{policy_key}/rule`
* `PATCH /policy/{policy_key}/rule/{rule_key}/target`

Each operation takes an array of objects, so you can create more than one at a time. 

!!! Note "A note about `PATCH` endpoints"
    The PATCH requests perform the equivalent of a `create_or_update` operation. This means that any existing objects sent to this endpoint will:

    - be updated,
    - any non-existing objects will be created, AND
    - any objects existing that are not specified in the request will not be deleted


## Create a Policy

Let's say you want to make a Policy that contains rules about a user's email address. You would start by first creating a Policy object:

```
PATCH /api/v1/policy

[
  {
    "name": "User Email Address",
    "key": "user_email_address_polcy",
    "drp_action": "access" // optional
  }
]
```
This policy is subtly different from the concept of a Policy in [Fidesctl](https://github.com/ethyca/fides). A [Fidesctl policy](https://ethyca.github.io/fides/language/resources/policy/) dictates which data categories can be stored where. A Fidesops policy, on the other hand, dictates how to access, mask or erase data that matches specific data categories for privacy requests.

### Policy Attributes
| Attribute | Description |
|---|---|
| `Policy.name` | User-friendly name for your Policy. |
| `Policy.key` | Unique key by which to reference the Policy. |
| `Policy.drp_action` | <b>Optional.</b> A [Data Rights Protocol](https://github.com/consumer-reports-digital-lab/data-rights-protocol) action to associate to this policy. |
| `access` | A data subject access request. Should be used with an `access` Rule. |
| `deletion` | A data subject erasure request. Should be used with an `erasure` Rule. |

## Add an Access Rule to your Policy
The policy creation operation returns a Policy key, which we'll use to add a Rule:

```
PATCH /api/v1/policy/{policy_key}/rule

[
  {
    "name": "Access User Email Address",
    "key": "access_user_email_address_rule",
    "action_type": "access",
    "storage_destination_key": "storage_key"
  }
]
```

Note that `storage_key` must identify an existing StorageConfig object.

Finally, we use the Rule key to add a Target:

```
PATCH /api/v1/policy/{policy_key}/rule/{rule_key}/target

[
  {
    "name": "Access User Email Address Target",
    "key": "access_user_email_address_target",
    "data_category": "user.provided.identifiable.contact.email",
  }
]
```

### Rule Attributes
- `Rule.action_type`: Which action is this `Rule` handling?
  - `access`: A data subject access request. A user would like to access their own data from within the Fidesops identity graph. Fidesops must look these fields up and return it to them. Fidesops will return these to a `storage_destination`.
  - `erasure`: A data subject erasure request (also known in some legislation as the Right to be Forgotten). A user would like to erase their own data currently stored in the Fidesops identity graph. Fidesops must look these fields up and either erase them entirely, or apply a `masking_strategy`.
- `Rule.storage_destination`: Where Fidesops will upload the returned data for an `access` action. Currently, Amazon S3 buckets and local filesystem storage are supported.
- `Rule.masking_strategy`: How to erase data in the Identity Graph that applies to this `Rule`. See [How-To: Configure Masking Strategies](masking_strategies.md) for a full list of supported strategies and their respective configurations.

## Add an Erasure Rule to your Policy
The simple access policy we've created above, will simply pull all data of category `user.provided.identifiable.contact.email`, but in the event of an erasure request, we might also want to mask this information. 

PATCH /api/v1/policy/{policy_key}/rule
```json
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
This will create a rule to hash a not-yet-specified value with a SHA-512 hash. We need to specify a target to hash, so we need to create a target for this rule:

PATCH api/v1/policy/{policy_key}/rule/{rule_key}
```json
  [
    {
      "data_category": "user.provided.identifiable.contact.email",
    },
  ]
```

This policy, `user_email_address_polcy`, will now do the following:
- Return all data inside the Identity Graph with a data category that matches (or is nested under) `user.provided.identifiable.contact`.
- Mask all data inside the Identity Graph with a data category that matches `user.provided.identifiable.contact.email` with a the `SHA-512` hashing function.

### A Note About Erasing Data

When a Policy Rule erases data, it erases the _entire_ branch given by the Target. For example, if we created an `erasure` rule with a Target of `user.provided.identifiable.contact`, _all_ of the information within the `contact` node -- including `user.provided.identifiable.contact.email` -- would be erased.

It's illegal to erase the same data twice within a Policy, so you should take care when you add Targets to a Rule. For example, you can't add `user.provided.identifiable.contact` _and_ `user.provided.identifiable.contact.email`
"data_category". 

And lastly, access rules will always run before erasure rules. 

