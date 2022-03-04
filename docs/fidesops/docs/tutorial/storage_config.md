# Set up Storage Destination


## Creating a StorageConfig 

For more detailed information, [see the Storage Config Guide](../guides/storage.md).

---
We need to configure a location to upload the user's PII after fidesops has retrieved it from the Flask App's
database. For tutorial purposes, we'll just write to a local file under `/fides_uploads`, but typically we'd want
to upload this to a Storage location like S3.  S3 would require a follow-up step to set up AWS access keys and secrets.

### Define helper method
```python
def create_local_storage(key, format, access_token):
    """
    Create a StorageConfig in fidesops to write to a local file. Returns the response JSON if successful.
    """
    storage_create_data = [
        {
            "name": key,
            "key": key,
            "type": "local",
            "format": format,
            "details": {
                "naming": "request_id",
            },
        },
    ]
    response = requests.patch(
        f"{FIDESOPS_URL}/api/v1/storage/config",
        headers=oauth_headers(access_token=access_token),
        json=storage_create_data,
    )
    logger.info(f"Defining an upload location. Status {response.status_code}")
    return response.json()

```

### Call helper method to set up Storage

This will define a local Storage location called `example_storage` that expects JSON data.  

```python
    if __name__ == "__main__":
        ...
        # Configure a Storage Config to upload the results
        create_local_storage(
            key="example_storage",
            format="json",
            access_token=access_token,
        )
        ...
```