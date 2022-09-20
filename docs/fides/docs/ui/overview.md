# Fides UI

Fides provides several user interfaces to assist in receiving and reviewing privacy requests, including options for managing your systems, datasets, and configuration settings. The Privacy Center and Admin UI work together to allow users to submit data subject requests (DSRs), which can then be fulfilled either automatically, or by privacy administrators.

## Admin UI
The Admin UI organizes processes like fulfilling [data subject requests](subject_requests.md), creating Fides resources, and [managing user access](user_management.md) into a single control panel. Once configured, the Admin UI allows authorized users to manage policies, [update datasets](datasets.md), and customize your Fides [taxonomy](https://ethyca.github.io/fideslang/taxonomy/overview/).

![admin ui](../img/admin_ui/admin_ui.png)

## Privacy Center 
The Fides [Privacy Center](privacy_center.md) is a configurable webpage that allows your users to submit data access or deletion requests. Requests submitted through the Privacy Center are available for review in the Admin UI, and are processed according to your policy execution rules.

![privacy center](../img/admin_ui/privacy_center.png)

## Configuration Wizard
The Fides [Configuration Wizard](wizard.md) provides a guided walkthrough for configuring Fides, connecting your infrastructure, and building your first data map. The Configuration Wizard covers an introduction to understanding privacy engineering fundamentals, as well as explaining Fides' terminology and resources.

![config wizard](../img/admin_ui/admin_ui_wizard.png)

## Access the UI
With Fides deployed, the hosted UI is available at `http://{server_url}/` (e.g. `http://localhost:8080/`) automatically. Review your root user [configuration](../installation/configuration.md) to verify your access credentials.