# Fideslog Analytics

Fidesops includes an implementation of [fideslog](https://github.com/ethyca/fideslog) to provide Ethyca with an understanding of user interactions with fides tooling. 

All collected analytics are anonymized, and only used in either product roadmap determination, or as insight into product adoption. Information collected by fideslog is received via HTTPs request, stored in a secure database, and never shared with third parties unless required by law.

More information on use, implementation, and configuration can be found in the [fideslog repository](https://github.com/ethyca/fideslog#readme).

## Collected Data
Fideslog collects information on instances of fidesops by recording internal events. Using fidesops may result in sending any or all of the following analytics data to Ethyca:  

| Parameter | Description |
|----|----|
| `docker` | If fidesops is run in a docker container. |
| `event` | The type of analytics event - currently, either a **server start** or **endpoint call**.
| `event_created` | The time of the event. |
| `endpoint` | The endpoint accessed. |
| `status_code` | The status result of the request. |
| `error` | Error information, if any. |

## Disabling Fideslog

To opt out of analytics, set either the following fidesops environment variable or `.toml` configuration variable to `True`. 

| Variable | Default | Use | 
|---|---|---|
| `analytics_opt_out` | False | Include in your `fidesops.toml` file. | 
| `FIDESOPS__USER__ANALYTICS_OPT_OUT` | False | Include in your environment variables. |

For more information, see the fidesops [configuration guide](../guides/configuration_reference.md).