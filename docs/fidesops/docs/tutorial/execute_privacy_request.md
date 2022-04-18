# Execute a Privacy Request


## See a Privacy Request in Action 

For more detailed information, [see the Privacy Request Guide](../guides/privacy_requests.md).

---

To summarize so far, we have:


    1) Created a client for authentication
    2) Created a connection from fidesops to our Flask App's Postgres Database
    3) Uploaded an annotated Dataset to fidesops so it knows how to traverse through the Flask App's tables
    4) Defined where to upload our user data after we've retrieved it from the Flask App
    5) Defined Policies describing what data we're looking for and what to do with that data.

For our last step, we'll write a method that will let us create a Privacy Request.  We need to specify the
Policy we want applied to that Privacy Request, as well as the starting identity of the user we'll need
to locate the remaining user information:

### Define helper method

```python
def create_privacy_request(email, policy_key):
    """
    Create a Privacy Request that is executed against the given request Policy.
    Returns the response JSON if successful, or throws an error otherwise.
    """

    privacy_request_data = [
        {
            "requested_at": datetime(2021, 1, 1).isoformat(),
            "policy_key": policy_key,
            "identity": {"email": email},
        },
    ]
    response = requests.post(
        f"{FIDESOPS_URL}/api/v1/privacy-request",
        json=privacy_request_data,
    )
    logger.info(f"Executing a Privacy Request. Status {response.status_code}")
    logger.info(f"Check fidesdemo/fides_uploads for upload package.")
    return response.json()
```

### Call helper method to run Privacy Request

This will create a request to fetch for all user data with category `user.provided.identifiable` associated 
with email `user@example.com` and save it to our local Storage destination, by specifying the email and the Policy.

```python
...
if __name__ == "__main__":
    ...
    # Execute a Privacy Request for user@example.com
    email = "user@example.com"
    privacy_requests = create_privacy_request(
        email=email,
        policy_key="example_request_policy",
    )
```

## Execute our Privacy Request

In your terminal, within the `fidesdemo` directory, we'll run our script to execute the Privacy Request:

```bash
python3 flaskr/fidesops.py
```

```bash
INFO:__main__:Creating access token. Status 200
INFO:__main__:Creating Oauth Client. Status 200
INFO:__main__:Adding scopes to oauth client. Status 200
INFO:__main__:Creating access token. Status 200
INFO:__main__:Creating PostgreSQL ConnectionConfig. Status 200
INFO:__main__:Updating PostgreSQL Secrets. Status 200.
INFO:__main__:Defining an upload location. Status 200
INFO:__main__:Creating an annotated Dataset. Status 200
INFO:__main__:Creating a Policy. Status 200
INFO:__main__:Creating a Rule. Status 200
INFO:__main__:Creating a Rule Target. Status 200
INFO:__main__:Executing a Privacy Request. Status 200
INFO:__main__:Check fidesdemo/fidesuploads for upload package.
```

Check your `fidesdemo/fides_uploads` directory for your data package (you may have to wait a few 
moments for the file to appear):

```json
{
  "flaskr_postgres_dataset:products": [
    {
      "description": "A description for example product #3",
      "name": "Example Product 3",
      "price": 50
    }
  ],
  "flaskr_postgres_dataset:purchases": [
    {
      "city": "Exampletown",
      "state": "NY",
      "street_1": "123 Example St",
      "street_2": "Apt 123",
      "zip": "12345"
    }
  ],
  "flaskr_postgres_dataset:users": [
    {
      "email": "user@example.com",
      "first_name": "Example",
      "last_name": "User",
      "password": "pbkdf2:sha256:260000$PGcBy5NzZeDdlu0b$a91ee29eefad98920fe47a6ef4d53b5abffe593300f766f02de041af93ae51f8"
    }
  ]
}
```

## Issues?
- Is `make server` running?
- [Reference the full script here](https://github.com/ethyca/fidesdemo/blob/main/flaskr/fidesops.py) for pieces you may be missing.
    - This script has more detailed logging and error handling.
- [Make sure your dataset is annotated properly](https://github.com/ethyca/fidesdemo/blob/main/fides_resources/flaskr_postgres_dataset.yml)
- Add breakpoints by inserting `import pdb; pdb.set_trace()` into the line where you want the breakpoint to set, then run your script.
    - Many of the endpoints used here are Bulk endpoints that return a 200 and then a mixture of a succeeded/failed resources.
- Check the docker logs:
```bash
docker ps
```
```bash
        Name                      Command               State                         Ports
------------------------------------------------------------------------------------------------------------------
fidesdemo_db_1         docker-entrypoint.sh postgres    Up      0.0.0.0:5432->5432/tcp,:::5432->5432/tcp
fidesdemo_fidesctl_1   fidesctl webserver               Up      0.0.0.0:8080->8080/tcp,:::8080->8080/tcp
fidesdemo_fidesops_1   fidesops webserver               Up      8000/tcp, 0.0.0.0:8000->8080/tcp,:::8000->8080/tcp
fidesdemo_redis_1      docker-entrypoint.sh redis ...   Up      0.0.0.0:6379->6379/tcp,:::6379->6379/tcp 
```
```bash
docker logs fidesdemo_fidesops_1
```