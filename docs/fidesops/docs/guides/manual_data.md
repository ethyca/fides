# Retrieve Manual Data for a Privacy Request

In this section we'll cover:

- How to describe a manual dataset
- How to send manual data to resume the access portion of a privacy request
- How to send manual data to resume the erasure portion of a privacy request

## Overview

Not all data can be automatically retrieved. When services have no external API, or when user data is held in a physical location, you can define a [dataset](datasets.md) to describe the types of manual fields you plan to upload, as well as any dependencies between these manual collections and other collections. 

When a manual dataset is defined, an in-progress access request will pause until the data is added manually, and then resume execution.

## Describing a manual dataset

In the following example, the Manual Dataset contains one `storage_unit` collection.  `email` is 
defined as the unit's [identity](datasets.md#field-members), which will then be used to retrieve the `box_id` in the storage unit.

To add a Manual Dataset, first create a [Manual ConnectionConfig](database_connectors.md#example-6-manual-connectionconfig). The following Manual Dataset can then be added to the new ConnectionConfig, with a [PATCH](database_connectors.md#associate-a-dataset) to `{{host}}/connection/<manual_key>/dataset`:

```yaml
dataset:
  - fides_key: manual_input
    name: Manual Dataset
    description: Example of a dataset whose data must be manually retrieved
    collections:
      - name: storage_unit
        fields:
          - name: box_id
            data_categories: [ user.provided ]
            fidesops_meta:
              primary_key: true
          - name: email
            data_categories: [ user.provided.identifiable.contact.email ]
            fidesops_meta:
              identity: email
              data_type: string
```

## Resuming a paused access privacy request

A privacy request will pause execution when it reaches a manual collection in an access request.  An administrator
should manually retrieve the data and send it in a POST request.  The fields 
should match the fields on the paused collection.  

Erasure requests with manual collections will also need data manually added as well.

```json title="<code>POST {{host}}/privacy-request/{{privacy_request_id}}/manual_input</code>"
[{
    "box_id": 5,
    "email": "customer-1@example.com"
}]
```

If no manual data can be found, simply pass in an empty list to resume the privacy request:

```json
[]
```

## Resuming a paused erasure privacy request

A privacy request will pause execution when it reaches a manual collection in an erasure request.  An administrator
should manually mask the records in question and send confirmation of the rows affected in a POST request.  

```json title="<code>POST {{host}}/privacy-request/{{privacy_request_id}}/erasure_confirm</code>"
{"row_count": 2}
```

If no manual data was destroyed, pass in a count of 0 to resume the privacy request:

```json
{"row_count": 0}
```