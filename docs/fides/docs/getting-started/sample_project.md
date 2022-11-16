# Run the Fides Sample Project

In order to get started quickly with Fides, a sample project is bundled within the Fides CLI that will set up a server, privacy center, and a sample application for you to experiment with.

To Fides in your own infrastructure, see the provided [DSR Automation](../dsr_quickstart/basic_setup.md) guide. 

## Deployment Steps

### Minimum requirements 

*  [Docker](https://www.docker.com/products/docker-desktop) (version 20.10.11 or later)
*  [Python](https://www.python.org/downloads/) (version 3.8 through 3.10) 
### Download and install Fides
You can easily download and install the Fides demo using `pip`. Run the following command to get started:

```
pip install ethyca-fides
```

### Deploy the Fides sample project
By default, Fides ships with a small project belonging to a fictional e-commerce store. Running the `deploy up` command builds a Fides project with all you need to run your first Data Subject Request against real databases.

```
fides deploy up
```

!!! Warning "If running `fides deploy` as part of a local fides development environment, refer to the [local documentation](../development/dev_deployment.md) instead."

### Exploring the sample project
When your deployment finishes, a welcome screen will explain the key components of Fides and the sample Cookie House store. 

If your browser does not open automatically, you should navigate to http://localhost:3000.

The project contains:

* The Fides [Admin UI](../ui/overview.md) for managing privacy requests
* The Fides [Privacy Center](../ui/privacy_center.md) for submitting requests
* The sample Cookie House eCommerce site for testing
* A DSR Directory on your computer to view results

### Run your first Privacy Access Request
Navigate to the Fides Privacy Center, type in the email address for the sample user (`jane@example.com`), and submit the request.

Then, navigate  to the Fides Admin UI to review the pending privacy request.

Approve the request, and review the resulting package! 

## Next steps
Congratulations! You've just run an entire privacy request in under 5 minutes! Fides offers many more tools help take control of your data privacy. To find out more, you can run a privacy request on [your own infrastructure](../dsr_quickstart/basic_setup.md), discover [data mapping](../guides/generate_datamaps.md), or learn about the [Fides Taxonomy](https://ethyca.github.io/fideslang/).