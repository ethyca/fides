# Fides Deploy Development

This guide closely mirrors the [Fides Deploy](../../getting-started/sample_project/) page with some slight differences to account for running in a development environment.

## Deployment Steps

1. If you haven't already, make sure to `pip install -e .` and `pip install nox`
1. `nox -s "build(sample)"` - This will build the relevant images and tag them correctly
1. `fides deploy up --no-pull` - This command will spin up the sample application and seed all relevant data as normal. The `--no-pull` flag prevents `Docker` from trying to pull remote images and will instead use the ones built with `"build(sample)"
1. Poke around and test as needed
1. Finally, run `fides deploy down` to teardown the application.
