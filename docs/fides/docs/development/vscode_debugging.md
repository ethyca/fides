# Debugging Fides in VSCode

This is a quick guide to show how VSCode can be used to debug Fides running locally in Docker. The general approach is to allow the local `fides` Docker Compose service to allow remote debugging connections, and to start a remote debugger from a host VSCode workspace.

## Setup

### Run Fides with Remote Debugging Enabled

In order to accept incoming remote debugging connections, the `fides` Docker Compose service must be run with slight alterations. To enable this functionality, simply add the `remote_debug` flag to a `nox` command. For example:

```
nox -s dev -- remote_debug
```
or 
```
nox -s dev -- remote_debug postgres timescale
```

With those commands, the `fides` Docker Compose service that's running the Fides server locally is able to accept incoming remote debugging connections.

Note that, at this point, the `remote_debug` flag is not enabled for other `nox` sessions, e.g. `fides_env`, `pytest_ops`, etc.

### Attach a Remote Debugger to the Fides Server 

Now that the running Fides server can accept incoming remote debugging connections, you can attach a remote debugger from a local VSCode workspace to actively debug the server application. A launch configuration is included in the `fides` repo to facilitate this step.

- Open up the `fides` repo in a VSCode workspace
- Go to the `Run and Debug` view
- From the debugger dropdown list, select the `Python debugger: Remote Attach Fides` configuration
- Click the `Start Debugging` play button
- The remote debugger should now be attached to the Fides server!
    - To confirm the debugger is attached, at least one `RUNNING` line item should appear in the `CALL STACK` window

## Debug!

At this point, VSCode is ready to debug the running Fides server. Try setting breakpoints and hitting them by, e.g., making certain HTTP requests against the Fides server. [This guide](https://code.visualstudio.com/docs/python/python-tutorial#_configure-and-run-the-debugger) provides more information on how to use the VSCode Python debugger. 

## Links

Some relevant VSCode documentation for reference:

- <https://code.visualstudio.com/docs/python/debugging#_debugging-by-attaching-over-a-network-connection>
- <https://code.visualstudio.com/docs/python/python-tutorial#_configure-and-run-the-debugger>
