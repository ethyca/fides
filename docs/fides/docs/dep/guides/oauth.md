# Authenticate with OAuth

When you invoke a Fides API, you must pass an _access token_ as the value of the `Authorization` header. This token must also include a _scope_ that gives you permission to take an action on the API. For example, to create a new execution policy, the token that you pass to the `Authorization` header must include the `policy:create_or_update` scope.

!!! Tip "When running the Fides webserver, navigate to the interactive API docs at `http://{server_url}/docs` (e.g., `http://0.0.0.0:8080/docs`) to access the following endpoints."
## Create the root client
Create an access client ID and secret for the "root" client. In your [`fides.toml`](../installation/configuration.md), these are defined as `oauth_root_client_id` and `oauth_root_client_secret`.

**The root client token contains all scopes,** and can call any of the Fides APIs. Once authenticated, creating additional users with individual scopes is recommended.

To create a root token, call the `POST /api/v1/oauth/token` endpoint:

```json title="<code>POST /api/v1/oauth/token</code>"
{
  "client_id": "{oauth_root_client_id}",
  "client_secret": "{oauth_root_client_secret}",
  "grant_type": "client_credentials"
}
```

```sh title="Curl options"
curl \
  -X POST 'http://<HOST>:8080/api/v1/oauth/token' \
  -d client_id={oauth_root_client_id} \
  -d client_secret={oauth_root_client_secret} \
  -d grant_type=client_credentials
```

Substitute the `oauth_root_client_id` and `oauth_root_client_secret` for the values in your `fides.toml`, or provide their environment variables.

If the `token` call is successful, the response will return the root client's access token in the `access_token` property:

```
HTTP/1.1 200 OK
Content-Type: application/json

{
  "access_token" : "MTI4Q0JDJSrgyplbmMiOiJBjU2I..._X0hTMyXAyPx",
  /* ignore any other properties */
}
```

## Create additional clients

Because the root client's token contains all scopes, it can create new clients and new client ID/client secret pairs which can be used to create additional access tokens.

!!! info "Best practices recommend creating a client with the scope `CLIENT_CREATE` to create any new clients. This will help to reduce the utilization of the all-scopes root client."

To create the client ID/secret pair, call `POST /api/v1/oauth/client`. If using the interactive Swagger docs, ensure you have provided your credentials in the **Authorize** option, and for the endpoint.

```sh title="Curl options"
curl \
  -X POST 'http://<HOST>:8080/api/v1/oauth/client' \
  -H 'Authorization: Bearer <root_access_token>'
  -H 'Content-Type: application/json'
  -d '{ "scopes": ["policy:read", "rule:read"]}'
```

The authorization header value is formed as `Bearer <token>`, and the request's `Content-Type` is `application/json`.
### Authorize a client with scopes

To add scopes to the client, the body of your request must contain an array of scope tokens.

You can retrieve the available scopes by calling [`GET /api/v1/oauth/scopes`](/api/index.md#operations-OAuth-read_scopes_api_v1_oauth_scope_get).

If the call is successful, Fides will respond with a new client ID/client secret pair:

```
HTTP/1.1 200 OK
Content-Type: application/json

{
  "client_id" : "<new_client_id>"
  "client_secret" : "<new_client_secret>",
}
```
## Create an access token
You then create a new access token by calling [`POST /api/v1/oauth/token`](../api/index.md#operations-OAuth-acquire_access_token_api_v1_oauth_token_post) with the new credentials.

In the above example, the new access token only lets the client read policies and rules. The client cannot create other clients, write policies, or perform other operations using Fides APIs.

### Access token expiration

By default, access tokens expire after 11520 minutes (8 days). To specify a different expiration time (in minutes) set the `OAUTH_ACCESS_TOKEN_EXPIRE_MINUTES` environment variable, or the `oauth_access_token_expire_minutes` value in your `fides.toml`.

If you call the Fides API with an expired token, the call returns `401`.

### Other OAuth Calls

Fides defines OAuth operations that let you delete a client, and read and write a client's scopes. See the [**OAuth** section of the **API** documentation](/api/index.md#operations-tag-OAuth) for details.
