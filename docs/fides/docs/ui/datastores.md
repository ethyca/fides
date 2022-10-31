# Managing Connections

Connections represent connected integrations to third party applications, databases and datasets, or manual storage locations.

![datastore](../img/admin_ui/datastore_list.png)

## Viewing Connections

All currently configured connections will appear in the paginated Connections panel. Search options are available to filter the list.

`Active` connections are included when fulfilling privacy requests.

`Disabled` connections have their connection information saved, but are not included when privacy requests are executed.

### Panel Options

| Option | Description |
|----|----|
| Search | Retrieve a connection by name. |
| Datastore Type | Filter connections by type: SaaS, Postgres, Mongo, etc. |
| System Type | Filter connections by system: SaaS, Database, or Manual. |
| Testing Status | Filter stores by the result of their last test: Passed, Failed, or Untested. |
| Status | Filter connections by status: Active or Disabled. |

## Testing Connections

Each configured connection includes an option to `Test` it. Fides will record the last tested time to the connections's card, and update the current connection status.

`Green` connections have passed their most recent test.

`Red` connections have failed.

`Grey` connections have not been tested.

![failed test](../img/admin_ui/failed_test.png)

## Disabling and Deleting Connections

Selecting the three dots menu `[...]` beside a connection will bring up `Disable` and `Delete` options for that connection.

![datastore options](../img/admin_ui/datastore_options.png)

Selecting either Disable or Delete will display a warning to confirm the action. Deleted connections will have their information removed entirely from Fides, while Disabled connections may be enabled again from the same menu at a later date.

![delete datastore](../img/admin_ui/delete_datastore.png)
