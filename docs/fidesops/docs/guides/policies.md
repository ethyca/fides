# How-To: Configure Request Policies

In this section we'll cover:

- An overview of request Policies
- How they differ from Policies in Fidesctl
- An overview of Policy Rules and RuleTargets
- How to create a simple Policy to access all user provided contact data
- How to extend this Policy to mask all user provided contact emails

Take me directly to [api docs](http://0.0.0.0:8080/docs#/Policy/create_or_update_policies_api_v1_policy_put).

## What is a request policy?

Request policies in Fidesops are pre-configured execution instructions for specific types of privacy requests. To put it simply they enable us to say "when Fidesops receives an identity from a source, apply an action to data within the identity graph that matches specific data categories, and upload the result to a destination".

#### How is this different from a Fidesctl Policy?

This is subtly different from the concept of a Policy in Fidesctl. A Fidesctl policy dictates which data categories can be stored where. A Fidesops policy dictates how to access, mask or erase data that matches specific data categories on a given privacy request.


## What is a Policy Rule?
In Fidesops a `Policy` is made up from a collection of `Rule`s. A `Rule` maps an `action_type` (either `erasure` or `access` are supported) to a `masking_strategy` or a `storage_destination`. To denote which data the `action_type`, `masking_strategy` or `storage_destination` should apply to, each `Rule` has a set of `RuleTarget`s (the Fideslang data categories we wish this data to apply to.). At privacy request execution time, the `Rule`s for a request's `Policy` are checked, and target data categories assembled alongside their corresponding fields in the `Dataset` before being passed into the Fidesops query builder (TODO: Insert link to query builder docs).

#### Rule attributes

- `Rule.action_type`: Which action is this `Rule` handling?
  - `access`: A data subject access request. A user would like to access their own data from within the Fidesops identity graph. Fidesops must look these fields up and return it to them. Fidesops will return these to a `storage_destination`.
  - `erasure`: A data subject erasure request (also known in some legislation as the Right to be Forgotten). A user would like to erase their own data currently stored in the Fidesops identity graph. Fidesops must look these fields up and either erase them entirely, or apply a `masking_strategy`.
- `Rule.storage_destination`: Where to upload the returned data. Currently Amazon S3 buckets and local filesystem storage are supported. Google Cloud Storage and Cloudflare S2 are on the near roadmap.
- `Rule.masking_strategy`: How to erase data in the Identity Graph that applies to this `Rule`. See [How-To: Configure Masking Strategies](masking_strategies.md) for a full list of supported strategies and their respective configurations.

#### Rule validation

`Rule` validation has the following constraints:

- An `access` rule must specify a pre-configured `storage_destination`. See [How-To: Configure Storage](storage.md) for more information.
- An `erasure` rule must specify a pre-configured `masking_strategy` See [How-To: Configure Masking Strategies](masking_strategies.md) for more information.
- Multiple `erasure` rules on the same `Policy` must not specify the same target. For example: two `Rule`s where `action_type` is set to `erasure` cannot target the `user.provided.identifiable.contact.name` data category, because Fidesops wouldn't know which action to apply first. Support for this is intended <> (TODO: Should we keep this sentence?).
  - Please note: Fideslang data categories are hierarchical, this has the following implications:
    - `user.provided.identifiable.contact` will automatically target all other data categories nested under it in the hierarcy, so this will include `user.provided.identifiable.contact.name`, `user.provided.identifiable.contact.address` and so forth.
    - `Rule` validation will treat any nested categories as conflicting targets, since `user.provided.identifiable.contact` is trying to target everything underneath it in the hierarchy, if we specify a separate erasure rule targetted at `user.provided.identifiable.contact.name` the Fidesops execution layer will have two options for erasing data that applies to the nested category (in this case `user.provided.identifiable.contact.name`). Support for this sccenario is intended <> (TODO: Should we keep this sentence?).


## Configure a simple read Policy

As mentioned above:
> An `access` rule must specify a pre-configured `storage_destination`.

To configure a storage destination, see [How-To: Configure Storage](storage.md) for more information.

#### Sample requests to create a Policy that will read all user provided identifiable contact information:

`PUT api/v1/policy`

```json 
[
  {
    "name": "A demo policy",
    "key": "a-demo-policy",
  },
]
```

#### Note:
- `storage_destination_key` should correspond to a previously configured storage destination object. See [How-To: Configure Storage](storage.md) for more information.

`PUT api/v1/policy/a-demo-policy/rule`

```json 
[
  {
    "name": "read identifiable contact data",
    "key": "read-identifiable-contact-data",
    "action_type": "access",
    "storage_destination_key": "your-preconfigured-storage-destination"
  },
]
```

`PUT api/v1/policy/a-demo-policy/rule/read-identifiable-contact-data`

```json 
[
  {
    "data_category": "user.provided.identifiable.contact",
  },
]
```

#### Adding an Erasure rule:

`PUT api/v1/policy/a-demo-policy/rule`

```json 
[
  {
    "name": "Mask Provided Emails",
    "key": "mask-provided-emails",
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

`PUT api/v1/policy/a-demo-policy/rule/mask-provided-emails`

```json 
[
  {
    "data_category": "user.provided.identifiable.contact.email",
  },
]
```

The `Policy` specified above will now:

- Return all data inside the Identity Graph with a data category that matches (or is nested under) `user.provided.identifiable.contact`.
- Mask all data inside the Identity Graph with a data category that matches `user.provided.identifiable.contact.email` with a the `SHA-512` hashing function.


For more comprehensive information on request Policies, please visit the [api docs](/docs#/Policy).