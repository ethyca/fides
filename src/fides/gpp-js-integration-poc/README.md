# GPP Integration POC

This is a POC to establish the viability of running a JS script to interact with the IAB GPP JS library, and call this Javascript script from a Python function.

## Running the POC

Run the fides backend as usual: `nox -s dev -- shell`.

In the fides container, go to the `gpp-js-integration-poc` folder: `cd gpp-js-integration-poc`.

Run the python script: `python gpp-helpers.py` .
