# Cypress component tests for fides-js

Component tests are a convenient way to render components individually without adding them to our app yet. Unfortunately, Cypress doesn't support preact out of the box. We'd have to write our own dev server configuration ([details](https://docs.cypress.io/guides/component-testing/component-framework-configuration#Custom-Dev-Server)). This means certain functionality will not work, for instance preact hooks. However, rendering basic React components works and can still be useful for development.
