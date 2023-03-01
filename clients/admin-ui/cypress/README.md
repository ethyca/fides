# Cypress

## Running

Most of the time, Cypress tests can be run as:

```
# Start the webapp
npm run start

# Start cypress in UI mode
npm run cy:open
```

However, because we do some [inter-zone navigation](https://github.com/ethyca/fides/blob/main/clients/admin-ui/src/features/common/zones/config.ts/#L12-L24) which Cypress will not handle due to security risks, sometimes it is important to run the webapp with `NODE_ENV=test`. We have a command `cy:start` which captures that, and also makes the server a little faster via a production build. This will potentially cause issues if testing manually with `fidesplus`, however the Cypress tests will run properly.

```
# Start the webapp in test mode
npm run cy:start

# Start cypress in UI mode
npm run cy:open
```
