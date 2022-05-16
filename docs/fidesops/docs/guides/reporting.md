# How-To: Report on Privacy Requests

In this section we'll cover:

- How to check the high-level status of your privacy requests
- How to get more detailed execution logs of collections and fields that were potentially affected as part of your privacy request.
- How to download all privacy requests as a CSV

Take me directly to [API docs](/fidesops/api#operations-Privacy_Requests-get_request_status_api_v1_privacy_request_get).


## Overview

The reporting feature allows you to fetch information about privacy requests. You can opt for high-level status 
information, or get more detailed information about the status of the requests on each of your collections.


## High-level Status


This request displays concise, high-level information for all your PrivacyRequests including their status and related timestamps.

Check out the [API docs here](/fidesops/api#operations-Privacy_Requests-get_request_status_api_v1_privacy_request_get).

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

`GET api/v1/privacy-request?request_id=<privacy_request_id>`

If an `external_id` was provided at request creation, we can also track the privacy request using:

`GET api/v1/privacy-request?external_id=<external_id>`

Please note: These parameters will return matching Privacy Requests based on startswith matches.

### Privacy Request Filtering Options

Use the following query params to further filter your privacy requests.  Filters can be chained, for example, 

`GET api/v1/privacy-request?created_gt=2021-10-01&created_lt=2021-10-05&status=pending`

- id
- status (one of `in_processing`, `pending`, `paused`, `complete`, or `error`)
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

Check out the [API docs here](/fidesops/api#operations-Privacy_Requests-get_request_status_logs_api_v1_privacy_request__privacy_request_id__log_get).


## View A Privacy Request's Identity Data

Use the optional `include_identities` query param to include all identity data that was submitted for the Privacy Request. Due to the nature of how Fidesops stores identity data, this data will expire automatically according to the `FIDESOPS__REDIS__DEFAULT_TTL_SECONDS` variable.

If the identity data fetched by `include_identities` has expired, an empty JSON dictionary will be returned.

## View Individual Privacy Request Log Details

Use the `verbose` query param to see more details about individual collections visited as part of the Privacy Request along
with individual statuses. Individual collection statuses include `in_processing`, `retrying`, `complete` or `error`.
You may see multiple logs for each collection as they reach different steps in the lifecycle.  

`verbose` will embed a “results” key in the response, with execution logs grouped by dataset name.  In the example below,
we have two datasets: `my-mongo-db` and `my-postgres-db`. There are two execution logs for `my-mongo-db` (when the `flights` 
collection is starting execution and when the `flights` collection has finished) and two execution
logs for `my-postgres-db` (when the `order` collection is starting and finishing execution).  `fields_affected` are the fields
that were potentially returned or masked based on the Rules you've specified on the Policy. The embedded execution logs 
are automatically truncated at 50 logs, so to view the entire list of logs, visit the execution logs endpoint separately.

`GET api/v1/privacy-request?request_id={privacy_request_id}&verbose=True`

```json
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
                                    "user.provided.identifiable.name"
                                ]
                            }
                        ],
                        "message": "success",
                        "action_type": "access",
                        "status": "complete",
                        "updated_at": "2022-02-28T16:38:04.727094+00:00"
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
                                    "user.provided.identifiable.name"
                                ]
                            }
                        ], 
                        "message": "success",
                        "action_type": "access",
                        "status": "complete",
                        "updated_at": "2022-02-28T16:39:04.668513+00:00"
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
## Downloading all privacy requests as a CSV 


To get all privacy requests in CSV format, use the `download_csv` query param:

`GET api/v1/privacy-request/?download_csv=True`

```csv
Time received,Subject identity,Policy key,Request status,Reviewer,Time approved/denied
2022-03-14 16:53:28.869258+00:00,{'email': 'customer-1@example.com'},my_primary_policy,complete,fid_16ffde2f-613b-4f79-bbae-41420b0f836b,2022-03-14 16:54:08.804283+00:00
```