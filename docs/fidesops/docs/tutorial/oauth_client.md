# Authentication

## Creating our Oauth Client

Our first step is to create an Oauth Client that we can use to authenticate all of our requests. For more detailed information, [see the Oauth Guide](../guides/oauth.md).

Add a method to our Python script that will call the fidesops API to create a token given a `client_id` and a `client_secret`:

### Define helper methods

```python title="<code>fidesdemo/flaskr/fidesops.py</code>"
def get_access_token(client_id, client_secret):
    """
    Authorize with fidesops via OAuth. Returns a valid access token if successful.
    """
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    response = requests.post(f"{FIDESOPS_URL}/api/v1/oauth/token", data=data)
    logger.info("Creating access token. Status %s", response.status_code)
    return response.json()["access_token"]
```

Add another method that will both create a client and assign scopes to that client. It's also useful to define a helper method to build Oauth headers at this point:

```python title="<code>fidesdemo/flaskr/fidesops.py</code>"
def oauth_headers(access_token):
    """Return valid authorization headers given the provided OAuth access token"""
    return {"Authorization": f"Bearer {access_token}"}
```

```python
def create_oauth_client(access_token):
    """
    Create a new OAuth client in fidesops.Returns the response JSON if successful.
    """

    # Here we're giving the client many scopes, but in a production app, just give the client the scopes they actually need.
    scopes_data = [
        "client:create",
        "client:update",
        "client:read",
        "client:delete",
        "policy:create_or_update",
        "policy:read",
        "policy:delete",
        "connection:create_or_update",
        "connection:read",
        "connection:delete",
        "privacy-request:read",
        "privacy-request:delete",
        "rule:create_or_update",
        "rule:read",
        "rule:delete",
        "storage:create_or_update",
        "storage:read",
        "storage:delete",
        "dataset:create_or_update",
        "dataset:read",
        "dataset:delete",
    ]
    response = requests.post(
        f"{FIDESOPS_URL}/api/v1/oauth/client", headers=oauth_headers(access_token), json=scopes_data
    )
    logger.info("Creating Oauth Client. Status %s", response.status_code)
    return response.json()

```

### Call helper methods to create an Oauth token

Update our script to call our new functions to create a token for the `root` client, and then use that token to create a *new* client 
with all the scopes.  Finally, we create another token for the new client, and that's what we'll use to 
authenticate subsequent requests.

Do not use the root client for anything other than creating other clients. 

`fidesdemo/flaskr/fidesops.py`
```python
...
if __name__ == "__main__":

     # Create a new OAuth client to use for our app
    root_token = get_access_token(
        client_id=ROOT_CLIENT_ID, client_secret=ROOT_CLIENT_SECRET
    )
    client = create_oauth_client(access_token=root_token)
    access_token = get_access_token(
        client_id=client["client_id"], client_secret=client["client_secret"]
    )

    ...
```
