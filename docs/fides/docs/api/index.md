# Fides Control API

The `fidesctl` API is almost completely programmatic, so it's easier to grasp the API by understanding the formula, rather than reading through a list of endpoints. The fundamental idea is that there's a set of five endpoints for each Fides resource. These endpoints let you...

| Purpose | Example | Success code |
| --- | --- | --- |
| Create an instance of a particular resource type. | `POST /policy` | `201` |
| Retrieve all instances of a resource type. | `GET /policy` | `200` |
| Retrieve the resource identified by the `fides_key` path parameter. |`GET /policy/{fides_key}` | `200`|
| Completely overwrite the `fides_key` resource.  |`POST /policy/{fides_key}`| `200` |
| Delete the `fides_key` resource. | `DELETE /policy/{fides_key}`| `204`|

* The URLs of the endpoints emulate the names of the resources: `/organization`, `/policy`, `/registry`, `/system`, `/dataset`, `/data_category`, `/data_use`, `/data_subject`, `/data_qualifier`, `/evaluation`.

* Except for the `DELETE`, the endpoints accept and/or return JSON objects that represent the named resource. The structure of these objects is given in the [Fides Language: Resources chapter](/language/resources/organization/) -- it's the same structure that's used in the resource manifest files.

That's about all there is to it. There are an additional four endpoints that we'll look at below, but the sets of quintuplet endpoints listed above make up the core of the `fidesctl` API.

After a brief review of the four addition endpoints, we'll provide a complete API reference followed by a set of cURL calls that you can use to exercise the API on your system.

## Other endpoints

The four additional endpoints are:

* `GET /health` pings the API server to see if it's up and running. The call returns `200` if it's up and ready to receive messages, and `404` if not.

* Three of the taxonomic resources, `/data_category`, `/data_use`, and `/data_qualifier` (but  _not_ `/data_subject`) define a `GET /resource_type/visualize/{figure_type}` endpoint that returns a graph of the resource's taxonomy.  For details, see the **API Reference**, below.

## API Reference

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