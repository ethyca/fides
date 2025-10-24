# FidesUI API Types

This folder is a psuedo version of the `types/api` folders that can be found in the Fides Admin UI. FidesUI only needs to know about some types, so we copy and paste the relevant ones to this folder. The contents of the files that go into `models` should be a result of typescript OpenAPI generation and should not be modified manually.

It may prove difficult to keep these types up to date, in which case we may want to keep _all_ generated types here, and have the apps that use `fidesui` import those types from `fidesui`.

For more information about typescript OpenAPI generation, see the [README in the Fides Admin UI](https://github.com/ethyca/fides/tree/main/clients/admin-ui/src/types/api).
