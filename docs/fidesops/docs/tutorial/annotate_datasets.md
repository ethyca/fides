# Create DatasetConfigs

## Annotate Datasets with fidesops_meta

For more detailed information, [see the Datasets Guide](../guides/datasets.md).

---

Next, fidesops needs to know how to traverse through our Flask App's database tables. 
We should upload a YAML file that describes our Flask App's database in a language that Fides understands.

See `fidesdemo/fides_resources/flaskr_postgres_dataset.yml` where we've already annotated the tables and fields in our Postgres
database with the relevant Data Categories.  We just need a few more annotations:

Add a `fidesops_meta` attribute to `flaskr_postgres_dataset.collections.seller_id`.  Fidesops will be able to take the users `id `
and use that to look up the `seller_id`.

```yaml
- name: seller_id 
  data_categories: [user.derived.identifiable.unique_id]
  fidesops_meta:
    references:
      - dataset: flaskr_postgres_dataset
        field: users.id
        direction: from
```

Similarly, add a `fidesops_meta` attribute to `flaskr_postgres_dataset.purchases.buyer_id`  Fidesops will be able
to take the user `id` and use that to look up purchases by `buyer_id`.

```yaml
- name: buyer_id
  data_categories: [user.derived.identifiable.unique_id]
  fidesops_meta:
    references:
      - dataset: flaskr_postgres_dataset
        field: users.id
        direction: from
```

Lastly, annotate `flaskr_postgres_dataset.users.email` field.   This is our entry point: Fidesops will first look up
the user by `email`, and from there, travel through other tables linked to `user`. 

```yaml
- name: email
  data_categories: [user.provided.identifiable.contact.email]
  fidesops_meta:
    identity: email
```

## Upload this Dataset to Fidesops

For more detailed information, [see the Datasets Guide](../guides/datasets.md).

---
We need to create a method that takes the Dataset we've just annotated and upload it to fidesops:

### Define helper method
```python
def create_dataset(connection_key, yaml_path, access_token):
    """
    Create a Dataset in fidesops given a YAML manifest file.
    Requires the `connection_key` for the PostgreSQL connection, and `yaml_path`
    that is a local filepath to a .yml Dataset Fides manifest file.
    Returns the response JSON if successful, or throws an error otherwise.
    See http://localhost:8000/api#operations-tag-Datasets
    """

    with open(yaml_path, "r") as file:
        dataset = yaml.safe_load(file).get("dataset", [])[0]

    dataset_create_data = [dataset]
    response = requests.put(
        f"{FIDESOPS_URL}/api/v1/connection/{connection_key}/dataset",
        headers=oauth_headers(access_token=access_token),
        json=dataset_create_data,
    )
    logger.info(f"Creating an annotated Dataset. Status {response.status_code}")
    return response.json()
```

### Call helper method to create a dataset

Our connection_key is the `flaskr_postgres` ConnectionConfig we created in the previous step,
and we're also passing in our completed YAML file:

```python
if __name__ == "__main__":
    ...
    # Upload the Dataset YAML for our PostgreSQL schema
    datasets = create_dataset(
        connection_key="flaskr_postgres",
        yaml_path="fides_resources/flaskr_postgres_dataset.yml",
        access_token=access_token,
    )
    ...
```
