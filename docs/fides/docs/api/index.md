# API Reference

You can view the live, interactive [Swagger](https://swagger.io/docs/) API docs for Fides by visiting `/docs` on a running instance. This is a great way to experiment with the APIs using Swagger's built-in "Try it out" functionality.

Below, we've embedded the latest release's API documentation as a living reference. These work largely the same, but since this documentation site isn't connected to a live instance, the "Try it out" and "Authorize" buttons won't work, sorry!

All API routes will automatically matched with and without a trailing slash `/`. So `/api/v1/config` and `/api/v1/config/` are both valid API calls.

---

!!swagger openapi.json!!

<script>
    /*If there is an anchor tag, reload it after the page loads to scroll to
     * that section, since the Swagger UI takes some time to render. */
    if (location.hash) {
        setTimeout(function() {
            location.href = location.href
        }, 200);
    }
</script>
