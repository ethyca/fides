# SaaS Post-Processors

Post-processors are, in essence, data transformers. Given data from an endpoint, we can add specific processors to transform the data into a format we need for privacy requests.

## Configuration

Post-processors are configured within the `endpoints` section of a `saas_config`:

```yaml
endpoints:
  - name: messages
    requests:
      read:
        method: GET
        path: /conversations/<id>/messages
        param_values:
          ...
        postprocessors:
          - strategy: unwrap
            configuration:
              data_path: conversation_messages
          - strategy: filter
            configuration:
              field: from_email
              value:
                identity: email
```

Note: Order matters as it's defined in the config. In the above example, unwrap will be run first, then the output of unwrap will be used in the filter strategy.

### Format subsequent requests

Post-processors can format the results of your access requests for use in subsequent update or delete statements.

For example, if we need to return the following in an access request:

```json
{"recipient": "test@email.com",
  "subscriptions": [{
    "id": "123",
    "subscribed": "TRUE"
  }]}
```

And we needed to perform an update request for each item within `subscriptions`, where `subscribed` = `TRUE`, then we'd need the following config for our update request:

```yaml
update:
    ...
    data_path: subscriptionStatuses
    postprocessors:
      - strategy: filter
        configuration:
          field: subscribed
          value: TRUE
```

## Supported Strategies
- `unwrap`: Gets object at given data path.
- `filter`: Removes data that does not match a given field and value.


### Filter

Filters object or array given field name and value. Value can reference a dynamic identity passed in through the request OR be a hard-coded value.

#### Configuration details

`strategy`: filter

`configuration`:

- `field` (_str_): Corresponds to the field on which to filter. For example, we wish to filter where `email_contact == "bob@mail.com"`, then `field` will be `email_contact`.
- `value` (_str_): Value to search for when filtering (e.g. hard-coded `bob@mail.com`) or Dict of identity path:
    - `identity` (_str_): Identity object from privacy request (e.g. `email` or `phone_number`)
- `exact` (optional _bool_ defaults to True): `value` and `field` value must be the same length (no extra characters).
- `case_sensitive` (optional _bool_ defaults to True): Cases must match between `value` and `field` value.

#### Examples

Post-Processor Config:
```yaml
- strategy: filter
  configuration:
    field: email_contact
    value:
      identity: email
```

Identity data passed in through request:

```json
{
  "email": "somebody@email.com"
}
```

Data to be processed:
```json
[
    {
        "id": 1397429347,
        "email_contact": "somebody@email.com",
        "name": "Somebody Awesome"
    },
    {
        "id": 238475234,
        "email_contact": "somebody-else@email.com",
        "name": "Somebody Cool"
    }
]
```

Result:
```json
[
    {
        "id": 1397429347,
        "email_contact": "somebody@email.com",
        "name": "Somebody Awesome"
    }
]
```
By default, this filter is exact and case-sensitive.

Post-Processor Config:
```yaml
- strategy: filter
  configuration:
    field: email_contact
    value:
      identity: email
    exact: False
    case_sensitive: False
```

Identity data passed in through request:

```json
{
  "email": "somebody@email.com"
}
```

Data to be processed:
```json
[
    {
        "id": 1397429347,
        "email_contact": "[Somebody Awesome] SOMEBODY@email.com",
        "name": "Somebody Awesome"
    },
    {
        "id": 1397429348,
        "email_contact": "somebody@email.com",
        "name": "Somebody Awesome"
    }
]
```

Result:
```json
[
    {
        "id": 1397429347,
        "email_contact": "[Somebody Awesome] SOMEBODY@email.com",
        "name": "Somebody Awesome"
    },
    {
        "id": 1397429348,
        "email_contact": "somebody@email.com",
        "name": "Somebody Awesome"
    }
]
```
We can configure how strict the filter is by setting `exact` and `case_sensitive` both to False. This allows our value to be a substring of a longer string, and to ignore case (upper vs lower case).

Note: Type casting is not supported at this time. We currently only support filtering by string values. e.g. `bob@mail.com` and not `12344245`.


### Unwrap

Given a path to a dict/list, returns the dict/list at that location.

#### Configuration details

`strategy`: unwrap

`configuration`:

- `data_path` (_str_): Gives the path to desired object. E.g. `exact_matches.members` will attempt to get the `members` object on the `exact_matches` object.


#### Example

Post-Processor Config:
```yaml
- strategy: unwrap
  configuration:
    data_path: exact_matches.members
```

Data to be processed:
```json
{
  "exact_matches": {
    "members": [
      { "howdy": 123 },
      { "meow": 841 }
    ]
  }
}   
```
Result:
```json
[
  { "howdy": 123 },
  { "meow": 841 }
]
```


