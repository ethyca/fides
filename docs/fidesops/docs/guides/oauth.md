# How-To: Authenticate with OAuth

In this section we'll cover:

- How to use the root client
- Creating additional OAuth clients using the root client
- Authorizing your client with scopes
- Creating OAuth tokens

When you invoke a Fidesops API, you must pass an _access token_ as the value of the `Authorization` header. Furthermore, the token must included a _scope_ that gives you permission to do take an action on the API. For example, let's say you want to create a new Policy by calling `PUT /api/v1/policy`. The token that you pass to the `Authorization` header must include the `policy:create_or_update` scope.

This document explains how to craft a properly-scoped access token.

## Getting Started

First, create an access token for the "root" client, included in the deployment by default. The root client's token is all-powerful: It contains all scopes so it can call any of the Fidesops APIs.

To create the root token, you pass the `OAUTH_ROOT_CLIENT_ID` and `OAUTH_ROOT_CLIENT_SECRET` environment variables (which are automatically defined in your system) to the `POST /api/v1/oauth/token` endpoint. You also set the `grant_type` parameter to `client_credentials`:

```
curl \
  -X POST 'http://<HOST>:8080/api/v1/oauth/token' \
  -d client_id=$OAUTH_ROOT_CLIENT_ID \
  -d client_secret=$OAUTH_ROOT_CLIENT_SECRET \
  -d grant_type=client_credentials
```

You'll notice that there's no `Authorization` header. This is the only Fidesops API that doesn't require an access token.

If the `token` call is successful, the response will return the root client's access token in the `access_token` property:

```
HTTP/1.1 200 OK
Content-Type: application/json

{
  "access_token" : "MTI4Q0JDJSrgyplbmMiOiJBjU2I..._X0hTMyXAyPx",
  /* ignore any other properties */
}
```

## Creating Additional Clients

Because the root client's token is all-powerful, it can create new clients and new client ID/client secret pairs which can be used to create additional access tokens. 

!!! Note "Pro Tip"
    For general best practices, we recommend creating a client with scope `CLIENT_CREATE` to create any new clients. This will help to reduce the utilization of the all-scopes root client.

To create the client ID/secret pair, call `POST /api/v1/oauth/client`:

```
curl \
  -X POST 'http://<HOST>:8080/api/v1/oauth/client' \
  -H 'Authorization: Bearer <root_access_token>'
  -H 'Content-Type: application/json'
  -d '{ "scopes": ["policy:read", "rule:read"]}'
```

For this call, we have to populate the `Authorization` header. Notice that the header's value is formed  as `Bearer <token>`. We also have to declare the request's `Content-Type` to be `application/json`.
### Authorize your Client with Scopes

To add scopes to the client, the body of your request must contain an array of scope tokens. 

You can retrieve the available scopes by calling [`GET /api/v1/oauth/scopes`](/api#operations-OAuth-read_scopes_api_v1_oauth_scope_get), or you can look in [the scope registry file](https://github.com/ethyca/solon/blob/main/src/fidesops/api/v1/scope_registry.py).

If the call is successful, Fidesapi responds with a new client ID/client secret pair:

```
HTTP/1.1 200 OK
Content-Type: application/json

{
  "client_id" : "<new_client_id>"
  "client_secret" : "<new_client_secret>",
}
```
## Create an Access Token
You then create a new access token by calling [`POST /api/v1/oauth/token`](/api#operations-OAuth-acquire_access_token_api_v1_oauth_token_post) with the new credentials. 

In the above example, your new access token only lets the client read policies and rules -- the client nor create other clients, nor write policies, nor perform other operations using Fidesops APIs.

### Access Token Expiration

By default, access tokens expire after 11520 minutes (8 days). To specify a different expiration time (in minutes) set the `OAUTH_ACCESS_TOKEN_EXPIRE_MINUTES` environment variable.

If you call a Fidesops API with an expired token, the call returns `401`.


### Other OAuth Calls

Fidesops defines OAuth operations that let you delete a client, and read and write a client's scopes. See the [**OAuth** section of the **API** documentation](/api#operations-tag-OAuth) for details. 


