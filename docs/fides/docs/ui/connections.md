# Manage Connections

Connections represent integrations to third party applications, databases and datasets, or manual storage locations.

![connection](../img/admin_ui/datastore_list.png)

## View Connections

All currently configured Connectors will appear in the paginated Connections panel. Search options are available to filter the connections list.

`Active` connections are included when fulfilling privacy requests.

`Disabled` connections have their connection information saved, but are not included when privacy requests are executed.

### Panel Options

| Option | Description |
|----|----|
| Search | Retrieve a connection by name. |
| Connection Type | Filter connections by type: SaaS, Postgres, Mongo, etc. |
| System Type | Filter connections by system: SaaS, Database, or Manual. |
| Testing Status | Filter stores by the result of their last test: Passed, Failed, or Untested. |
| Status | Filter connections by status: Active or Disabled. |

## Add a connection

To add a new connection, select "**Create New Connector**" from the Connections panel. You will be directed to a list of all available connection options, including adding [manual connectors](#manual-connections).

![new connection](../img/admin_ui/new_connection.png)

Search for and select your desired connector. The connections UI will assist in adding and configuring your new connection. 

### Automated connections

Fides automatically includes your SaaS connectors when processing [privacy requests](../getting-started/privacy_requests.md). Once you have selected a connection type, the UI allows you to describe your connection's configuration information, which includes any necessary fields for accessing and updating third-party data.

![configure connection](../img/admin_ui/configure_connection.png)

Once you have filled in the necessary information, select **Save**, and Fides will automatically attempt to test your connection.

### Manual connections

Manual connections are available for any data that cannot be processed automatically. Examples of manual connections might include physical storage locations, or third-party services without accessible APIs. Fides will pause processing a privacy request at any manual connection, and wait for administrator input before continuing.

To add a manual connection, select **Manual connection** in the "Show all connectors" dropdown. 

![manual connection](../img/admin_ui/manual_connection.png)

Once selected, Fides allows you to name and describe your manual connection, as well as provide a list of connection owners. These owners will be contacted by email when needed to respond to a privacy request with a manual component.

To continue, select **Save**.

![manual configuration](../img/admin_ui/manual_configuration.png)

You may now add any fields required by the manual connection. Connection owners will be required to supply this information when processing a manual request.

Additional fields may be added by selecting **Add new PII Fields**. 

![manual fields](../img/admin_ui/manual_fields.png)

One finished, select **Save.**
## Test a connection

Each configured connection includes an option to `Test` its connection. Fides will record the last tested time to the connection's card, and update the current connection status.

`Green` connections have passed their most recent test.

`Red` connections have failed.

`Grey` connections have not been tested.

![failed test](../img/admin_ui/failed_test.png)

## Disable and delete connections

Selecting the three dots menu `[...]` beside a connection's status will bring up `Disable` and `Delete` options for that connection.

![connection options](../img/admin_ui/datastore_options.png)

Selecting either Disable or Delete will display a warning to confirm the action. Deleted connections will have their information removed entirely from fides.api, while Disabled connections may be enabled again from the same menu at a later date.

![delete connections](../img/admin_ui/delete_datastore.png)
