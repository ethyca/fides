# Report on Privacy Requests
## Overview

The reporting feature allows you to fetch information about privacy requests. You can opt for high-level status 
information, or get more detailed information about the status of the requests on each of your collections.


## View high-level statuses

This request displays concise, high-level information for all your privacy requests including their status and related timestamps.

View he [API docs here](../api/index.md#operations-Privacy_Requests-get_request_status_api_v1_privacy_request_get).

```json title="<code>GET api/v1/privacy-request</code>"
{
    "items": [
        {
            "id": "pri_5f4feff5-fb60-4286-82bd-7e0748ce90ac",
            "created_at": "2021-10-04T17:36:32.223287+00:00",
            "started_processing_at": "2021-10-04T17:36:37.248880+00:00",
            "finished_processing_at": "2021-10-04T17:36:37.263121+00:00",
            "status": "pending"
        }
    ],
    "total": 1,
    "page": 1,
    "size": 50
}
```

### View a single privacy request

Use the `id` query param to view the high level status of a single privacy request.

```
GET api/v1/privacy-request?request_id=<privacy_request_id>
```

If an `external_id` was provided at request creation, we can also track the privacy request using:

```
GET api/v1/privacy-request?external_id=<external_id>
```

!!! Note "These parameters will return matching privacy requests based on `startswith` matches."

### Filtering options

Use the following query params to further filter your privacy requests.  Filters can be chained, for example, 

```
GET api/v1/privacy-request?created_gt=2021-10-01&created_lt=2021-10-05&status=pending
```

- `id`
- status (one of `in_processing`, `pending`, `paused`, `complete`, or `error`)
- `created_lt`
- `created_gt`
- `started_lt`
- `started_gt`
- `completed_lt`
- `completed_gt`
- `errored_lt`
- `errored_gt`

You can filter for multiple statuses by repeating the status query param:

```
GET api/v1/privacy-request?status=paused&status=complete
```



## View privacy request logs

To view all the execution logs for a privacy request, visit `/api/v1/privacy-request/{privacy_request_id}/logs`.
Embedded logs in the previous endpoints are truncated at 50 logs.

View the [API docs here](../api/index.md#operations-Privacy_Requests-get_request_status_logs_api_v1_privacy_request__privacy_request_id__log_get).


## View a request's identity data
Use the optional `include_identities` query param to include all identity data that was submitted for the privacy request. Due to the way Fides stores identity data, this data will expire automatically according to the `FIDES__REDIS__DEFAULT_TTL_SECONDS` variable in your Fides [config](../installation/configuration.md).

If the identity data fetched by `include_identities` has expired, an empty JSON dictionary will be returned.

## View individual request log details
The `verbose` query parameter will display more details about individual collections visited as part of the privacy request, along with individual statuses. Individual collection statuses include `in_processing`, `retrying`, `complete` or `error`. You may see multiple logs for each collection as they reach different steps in the lifecycle.  

The `verbose` parameter will embed a “results” key in the response, with both audit logs containing information about the overall request, as well as execution logs grouped by dataset name.  

In the example below, there are two datasets: `my-mongo-db` and `my-postgres-db`. There are two execution logs for `my-mongo-db` (when the `flights` collection is starting execution, and when the `flights` collection has finished), and two execution
logs for `my-postgres-db` (when the `order` collection is starting and finishing execution). The `fields_affected` are the fields
that were potentially returned or masked based on the [Rules](../getting-started/execution_policies.md#add-a-rule) you've specified on the execution policy. 

The embedded execution logs are automatically truncated at 50 logs. To view the entire list of logs, visit the execution logs endpoint separately. "Request approved" and "Request finished" audit logs are also included in the response.

```json title="<code>GET api/v1/privacy-request?request_id={privacy_request_id}&verbose=True</code>"
{
    "items": [
        {
            "id": "pri_2e0655c3-7a76-425e-8c4c-52fee32ce14b",
            "created_at": "2022-02-28T16:38:03.878898+00:00",
            "started_processing_at": "2022-02-28T16:38:04.021763+00:00",
            "finished_processing_at": "2022-02-28T16:38:06.211547+00:00",
            "status": "complete",
            "external_id": null,
            "results": {
                 "Request approved": [
                    {
                        "collection_name": null,
                        "fields_affected": null,
                        "message": "",
                        "action_type": null,
                        "status": "approved",
                        "updated_at": "2022-08-11T14:03:37.679732+00:00",
                        "user_id": "system"
                    }
                ],
                "my-mongo-db": [
                    {
                        "collection_name": "flights",
                        "fields_affected": [],
                        "message": "starting",
                        "action_type": "access",
                        "status": "in_processing",
                        "updated_at": "2022-02-28T16:38:04.668513+00:00"
                    },
                     {
                        "collection_name": "flights",
                        "fields_affected": [
                            {
                                "path": "mongo_test:flights:passenger_information.full_name",
                                "field_name": "passenger_information.full_name",
                                "data_categories": [
                                    "user.name"
                                ]
                            }
                        ],
                        "message": "success",
                        "action_type": "access",
                        "status": "complete",
                        "updated_at": "2022-02-28T16:38:04.727094+00:00",
                        "user_id": null
                    }
                ],
                "my-postgres-db": [
                    {
                        "collection_name": "order",
                        "fields_affected": [],
                        "message": "starting",
                        "action_type": "access",
                        "status": "in_processing",
                        "updated_at": "2022-02-28T16:38:04.668513+00:00"
                    },
                    {
                        "collection_name": "order",
                        "fields_affected": [
                            {
                                "path": "order.customer_name",
                                "field_name": "name",
                                "data_categories": [
                                    "user.name"
                                ]
                            }
                        ], 
                        "message": "success",
                        "action_type": "access",
                        "status": "complete",
                        "updated_at": "2022-02-28T16:39:04.668513+00:00",
                        "user_id": null
                    }
                ]
            },
            "Request finished": [
                {
                    "collection_name": null,
                    "fields_affected": null,
                    "message": "",
                    "action_type": null,
                    "status": "finished",
                    "updated_at": "2022-08-11T14:04:29.611878+00:00",
                    "user_id": "system"
                }
            ]
        }
    ],
    "total": 1,
    "page": 1,
    "size": 50
}


```
## Download all privacy requests as a CSV 
To get all privacy requests in CSV format, use the `download_csv` query param:


```csv title="<code>GET api/v1/privacy-request/?download_csv=True</code>"
Time received,Subject identity,Policy key,Request status,Reviewer,Time approved/denied
2022-03-14 16:53:28.869258+00:00,{'email': 'customer-1@example.com'},my_primary_policy,complete,fid_16ffde2f-613b-4f79-bbae-41420b0f836b,2022-03-14 16:54:08.804283+00:00
```

## Paused or failed request details
A privacy request may pause when manual input is needed from the user, or it might fail for various reasons on a specific collection.  

To retrieve information to resume or retry a privacy request, the following endpoint is available:
 ```
 GET api/v1/privacy-request?request_id=<privacy_request_id>
 ```

### Paused access request example
The request below is in a `paused` state as it waits on manual input from the user to proceed. Looking at the `stopped_collection_details` key shows the request paused execution during the `access` step of the `manual_key:filing_cabinet` collection. 

The `action_needed.locators` field shows the user they should fetch the record in the filing cabinet with a `customer_id` of `72909`, and pull the `authorized_user`, `customer_id`, `id`, and `payment_card_id` fields from that record. These values should be manually uploaded to the `resume_endpoint`. 

See the [manual data guides](../getting-started/datasets.md#resume-a-paused-access-privacy-request) for more information on resuming a paused access request.
                          

```json
{
    "items": [
        {
            "id": "pri_ed4a6b7d-deab-489a-9a9f-9c2b19cd0713",
            "created_at": "2022-06-06T20:12:28.809815+00:00",
            "started_processing_at": "2022-06-06T20:12:28.986462+00:00",
            ...,
            "stopped_collection_details": {
                "step": "access",
                "collection": "manual_key:filing_cabinet",
                "action_needed": [
                    {
                        "locators": {
                            "customer_id": [
                                72909
                            ]
                        },
                        "get": [
                            "authorized_user",
                            "customer_id",
                            "id",
                            "payment_card_id"
                        ],
                        "update": null
                    }
                ]
            },
            "resume_endpoint": "/privacy-request/pri_ed4a6b7d-deab-489a-9a9f-9c2b19cd0713/manual_input"
        }
    ],
    "total": 1,
    "page": 1,
    "size": 50
}
```

### Paused erasure request example

The request below is in a `paused` state for user to confirm they've masked the appropriate data before proceeding. 

The `stopped_collection_details` shows that the request paused execution during the `erasure` step of the `manual_key:filing_cabinet` collection. Looking at `action_needed.locators` field shows that the user should find the record in the filing cabinet with an `id` of 2, and replace its `authorized_user` with `None`. 

A confirmation of the masked records count should be uploaded to the `resume_endpoint`. See the [manual data guides](../getting-started/datasets.md#resume-a-paused-erasure-privacy-request) for more information on resuming a paused erasure request.
              
```json
{
    "items": [
        {
            "id": "pri_59ea0129-fc6d-4a12-a5bd-2ee647bf5cec",
            "created_at": "2022-06-06T20:22:05.436361+00:00",
            "started_processing_at": "2022-06-06T20:22:05.473280+00:00",
            "finished_processing_at": null,
            "status": "paused",
            ...,
            "stopped_collection_details": {
                "step": "erasure",
                "collection": "manual_key:filing_cabinet",
                "action_needed": [
                    {
                        "locators": {
                            "id": 2
                        },
                        "get": null,
                        "update": {
                            "authorized_user": null
                        }
                    }
                ]
            },
            "resume_endpoint": "/privacy-request/pri_59ea0129-fc6d-4a12-a5bd-2ee647bf5cec/erasure_confirm"
        }
    ],
    "total": 1,
    "page": 1,
    "size": 50
}


```

### Failed request example

The below request is an `error` state because something failed in the `erasure` step of the `postgres_dataset:payment_card` collection.  

After troubleshooting the issues with your postgres connection, resume the request with a POST to the `resume_endpoint`.

```json
{
    "items": [
        {
            "id": "pri_59ea0129-fc6d-4a12-a5bd-2ee647bf5cec",
            "created_at": "2022-06-06T20:22:05.436361+00:00",
            "started_processing_at": "2022-06-06T20:22:05.473280+00:00",
            "finished_processing_at": null,
            "status": "error",
            ...,
            "stopped_collection_details": {
              "step": "erasure",
              "collection": "postgres_dataset:payment_card",
              "action_needed": null
            },
            "resume_endpoint": "/privacy-request/pri_59ea0129-fc6d-4a12-a5bd-2ee647bf5cec/retry"
        }
    ],
    "total": 1,
    "page": 1,
    "size": 50
}

```
