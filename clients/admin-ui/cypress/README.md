# Cypress

## Running

Most of the time, Cypress tests can be run as:

```
# Start the webapp
turbo run start

# Start cypress in UI mode
turbo run cy:open
```

To run against a production build of the app (faster, but no hot reloading):

```
# Start the webapp in test mode
turbo run cy:start

# Start cypress in UI mode
turbo run cy:open
```
