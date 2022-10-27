# Fides Deploy

In order to get up-and-running quickly with a demo version of fides, we've shipped a sample application within fides that will configure and start all of the components for you.

## Deployment Steps

1. If you haven't already, make sure to `pip install ethyca-fides`
1. `fides deploy up` - This command will verify your Docker version compatibility (an upgrade may be required), as well as pull the required Docker versions. There will be a success welcome message once the startup is complete.
1. Finally, run `fides deploy down` to teardown the application. Congratulations, you've completed the fides sample tutorial!

!!! Warning "If running `fides deploy` as part of a local fides development environment, refer to [this page](../development/dev_deployment.md) instead."
