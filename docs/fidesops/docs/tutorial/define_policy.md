# Define Policies

## Creating a Policy with Rules and Targets 
For more detailed information, [see the Policy Guide](../guides/policies.md).

---

We're almost there: we need to create a Policy to describe how to handle a Privacy Request.

Very detailed configurations are supported to define how different data is treated. You can create 
Policies with multiple Rules (how the data is handled), that each have Rule Targets (what data we care about). 

Below are methods to add a Policy, a Rule, and a Rule Target, plus a cleanup method that deletes Rules for
convenience (handy if you'll be running this script multiple times).

### Define helper methods

```python
def create_policy(key, access_token):
    """
    Create a request policy in fidesops with the given key.Returns the response JSON if successful, or throws an error otherwise.
    """

    policy_create_data = [
        {
            "name": key,
            "key": key,
        },
    ]
    response = requests.patch(
        f"{FIDESOPS_URL}/api/v1/policy",
        headers=oauth_headers(access_token=access_token),
        json=policy_create_data,
    )
    logger.info(f"Creating a Policy. Status {response.status_code}")
    return response.json()
```   

```python
def create_policy_rule(
        policy_key, key, action_type, storage_destination_key, access_token
):
    """
    Create a Policy Rule to return matched data in an access request to the given Storage destination.
    Returns the response JSON if successful, or throws an error otherwise.
    """

    rule_create_data = [
        {
            "name": key,
            "key": key,
            "action_type": action_type,
            "storage_destination_key": storage_destination_key,
        },
    ]
    response = requests.patch(
        f"{FIDESOPS_URL}/api/v1/policy/{policy_key}/rule",
        headers=oauth_headers(access_token=access_token),
        json=rule_create_data,
    )

    logger.info(f"Creating a rule. Status {response.status_code}")
    return response.json()
```    

```python
def create_policy_rule_target(policy_key, rule_key, data_category, access_token):
    """
    Create a Policy Rule Target that matches the given data_category.
    Returns the response JSON if successful, or throws an error otherwise.
    """

    target_create_data = [
        {
            "data_category": data_category,
        },
    ]
    response = requests.patch(
        f"{FIDESOPS_URL}/api/v1/policy/{policy_key}/rule/{rule_key}/target",
        headers=oauth_headers(access_token=access_token),
        json=target_create_data,
    )

    logger.info(f"Creating a Rule Target. Status {response.status_code}")
    return response.json()
```
```python
def delete_policy_rule(policy_key, key, access_token):
    """
    Deletes a Policy rule with the given key.
    Returns the response JSON.
    """
    return requests.delete(
        f"{FIDESOPS_URL}/api/v1/policy/{policy_key}/rule/{key}",
        headers=oauth_headers(access_token=access_token),
    )
```

### Call helper methods to create the Policy

For simplicity's sake, let's just create one Policy, one Rule, and one Target.

Our single Policy will have one Rule with type `access`, meaning we just want to *retrieve* user data, not delete it. 
We also configure on the Rule that any results will be uploaded to our local Storage `example_storage`.

Finally, we create a RuleTarget, that is looking for all data with the category `user.provided.identifiable` (and included subcategories). 

```python
if __name__ == "__main__":
  ...
 # Create a Policy that returns all user data
    policy = create_policy(
        key="example_request_policy",
        access_token=access_token,
    )
    delete_policy_rule("example_request_policy", "access_user_data", access_token)
    create_policy_rule(
        policy_key="example_request_policy",
        key="access_user_data",
        action_type="access",
        storage_destination_key="example_storage",
        access_token=access_token,
    )

    data_category = "user.provided.identifiable"
    create_policy_rule_target(
        "example_request_policy", "access_user_data", data_category, access_token
    )

```

If you look back at our annotated YAML `fides_resources/flaskr_postgres_dataset.yml`, we can see the relevant fields
associated with this Data Category that we will expect in our final upload package:

- `products` collection:  `description`,`name`, and `price` 
- `user` collection: `email`, `first_name`, `last_name`, and `password`
- `purchases` collection`: `city`, `state`, `street_1`, `street_2`, and `zip`
