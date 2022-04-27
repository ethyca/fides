# SaaS Post-Processors

Post-processors are, in essence, data transformers. Given data from an endpoint, we can add specific processors to transform the data into a format we need for subject requests.

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

### For Update/Delete/GDPR endpoints

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
          subscribed: TRUE
```

## Supported Strategies
- `unwrap`: Gets object at given data path.
- `filter`: Removes data that does not match a given field and value.


### Filter

Filters object or array given field name and value. Value can reference a dynamic identity passed in through the request OR be a hard-coded value.

#### Configuration Details

`strategy`: filter

`configuration`:

- `field` (_str_): Corresponds to the field on which to filter. For example, we wish to filter where `email_contact == "bob@mail.com"`, then `field` will be `email_contact`. Note that filtering an array by a field that's deeply nested is not yet supported.
- `value` (_str_): Value to search for when filtering (e.g. hard-coded `bob@mail.com`) or Dict of identity path:
    - `identity` (_str_): Identity object from subject request (e.g. `email` or `phone_number`)


#### Example

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

Note: Type casting is not supported at this time. We currently only support filtering by string values. e.g. `bob@mail.com` and not `12344245`.


### Unwrap

Given a path to a dict/list, returns the dict/list at that location.

#### Configuration Details

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


