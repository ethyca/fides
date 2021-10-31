# How-To: Report on Privacy Requests

In this section we'll cover:

- How to check the high-level status of your privacy requests
- How to get more detailed execution logs of queries that were run as part of your privacy requests. 


Take me directly to [API docs](/api#operations-Privacy_Requests-get_request_status_api_v1_privacy_request_get).


## Overview

The reporting feature allows you to fetch information about privacy requests. You can opt for high-level or more detailed 
information about the individual queries executed internally.


## High-level Status


This request displays concise, high-level information for all your PrivacyRequests including their status and related timestamps.

Check out the [API docs here](/api#operations-Privacy_Requests-get_request_status_api_v1_privacy_request_get).

`GET api/v1/privacy-request`

```json
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

### Single Privacy Request

Use the `id` query param to view the high level status of a single privacy request.

`GET api/v1/privacy-request?id=<privacy_request_id>`

If an `external_id` was provided at request creation, we can also track the privacy request using:

`GET api/v1/privacy-request?external_id=<external_id>`

### Privacy Request Filtering Options

Use the following query params to further filter your privacy requests.  Filters can be chained, for example, 

`GET api/v1/privacy-request?created_gt=2021-10-01&created_lt=2021-10-05&status=pending`

- id
- status (one of `in_processing`, `pending`, `complete`, or `error`)
- created_lt
- created_gt
- started_lt
- started_gt
- completed_lt
- completed_gt
- errored_lt
- errored_gt

## View All Privacy Request Logs

To view all the execution logs for a Privacy Request, visit `/api/v1/privacy-request/{privacy_request_id}/logs`.
Embedded logs in the previous endpoints are truncated at 50 logs.

Check out the [API docs here](/api#operations-Privacy_Requests-get_request_status_logs_api_v1_privacy_request__privacy_request_id__log_get).

## View Individual Privacy Request Log Details

Use the `verbose` query param to see more details about individual queries run as part of the Privacy Request along
with individual statuses. 

`verbose` will embed a “results” key in the response, with execution logs grouped by dataset name.  In the example below,
we have two datasets: `my-mongo-db` and `my-postgres-db`. There is one execution log for my-mongo-db and two execution
logs for my-postgres-db.  The embedded execution logs are automatically truncated at 50 logs, so to view the entire 
list of logs, visit the execution logs endpoint separately.

`GET api/v1/privacy-request?verbose=True`

```json
{
    "items": [
        {
            "id": "pri_5f4feff5-fb60-4286-82bd-7e0748ce90ac",
            "created_at": "2021-10-04T17:36:32.223287+00:00",
            "started_processing_at": "2021-10-04T17:36:37.248880+00:00",
            "finished_processing_at": "2021-10-04T17:36:37.263121+00:00",
            "status": "pending",
            "results": {
                "my-mongo-db": [
                    {
                        "collection_name": "order",
                        "fields_affected": [
                            {
                                "path": "order.customer_name",
                                "field_name": "name",
                                "data_categories": [
                                    "user.provided.identifiable.name"
                                ]
                            }
                        ],
                        "message": null,
                        "action_type": "access",
                        "status": "pending",
                        "updated_at": "2021-10-05T18:24:55.570430+00:00"
                    }
                ],
                "my-postgres-db": [
                    {
                        "collection_name": "order",
                        "fields_affected": [
                            {
                                "path": "order.customer_name",
                                "field_name": "name",
                                "data_categories": [
                                    "user.provided.identifiable.name"
                                ]
                            }
                        ],
                        "message": null,
                        "action_type": "access",
                        "status": "pending",
                        "updated_at": "2021-10-05T18:24:39.953914+00:00"
                    },
                    {
                        "collection_name": "order",
                        "fields_affected": [
                            {
                                "path": "order.customer_name",
                                "field_name": "name",
                                "data_categories": [
                                    "user.provided.identifiable.name"
                                ]
                            }
                        ],
                        "message": null,
                        "action_type": "access",
                        "status": "pending",
                        "updated_at": "2021-10-05T18:24:45.240612+00:00"
                    }
                ]
            }
        }
    ],
    "total": 1,
    "page": 1,
    "size": 50
}


```
