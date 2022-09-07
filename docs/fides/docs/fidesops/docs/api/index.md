# API Reference

You can view the live, interactive [Swagger](https://swagger.io/docs/) API docs for fidesops by visiting `/docs` on a running instance. This is a great way to experiment with the APIs using Swagger's built-in "Try it out" functionality.
Additionally, you can download our [fidesops Postman collection](../postman/Fidesops.postman_collection.json) and [follow instructions
to set up on your machine](../postman/using_postman.md).

Below, we've embedded the latest release's API documentation as a living reference. These work largely the same, but since this documentation site isn't connected to a live instance, the "Try it out" and "Authorize" buttons won't work, sorry!

All fidesops api routes will automatically match with and without a trailing slash `/`. So `/api/v1/config` and `/api/v1/config/` are both valid API calls.

## Swagger API Docs
---
!!swagger openapi.json!!

<script>
    /* If there is an anchor tag, reload it after the page loads to scroll to
     * that section, since the Swagger UI takes some time to render. */
    if (location.hash) {
        setTimeout(function() {
            location.href = location.href
        }, 200);
    }
</script>