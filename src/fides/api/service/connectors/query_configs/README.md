## Understanding the `BigQueryQueryConfig.generate_update` Method

### Example: Handling Nested Data and Arrays

Consider this original row in BigQuery:

```python
# Original row data
row = {
    "user_id": 123,
    "profile": {
        "name": "John Doe",
        "email": "john@example.com",
        "preferences": {
            "theme": "dark",
            "notifications": True
        },
        "tags": ["customer", "premium", "active"]
    },
    "activity": {
        "last_login": "2023-05-15",
        "login_count": 42
    }
}
```

And a masking update:

```python
update_value_map = {
    "profile.email": "REDACTED",
    "profile.preferences.notifications": None,
    "profile.tags.0": None,  # Null first tag
    "profile.tags.1": None,  # Null second tag
    "profile.tags.2": None   # Null third tag
}
```

### Step-by-Step Process

#### Step 1: Take `update_value_map` as-is
```python
# update_value_map with array indexes
{
    "profile.email": "REDACTED",
    "profile.preferences.notifications": None,
    "profile.tags.0": None,
    "profile.tags.1": None,
    "profile.tags.2": None
}
```

#### Step 2: Flatten the row with array indexes
```python
flattened_row = {
    "user_id": 123,
    "profile.name": "John Doe",
    "profile.email": "john@example.com",
    "profile.preferences.theme": "dark",
    "profile.preferences.notifications": True,
    "profile.tags.0": "customer",
    "profile.tags.1": "premium",
    "profile.tags.2": "active",
    "activity.last_login": "2023-05-15",
    "activity.login_count": 42
}
```

#### Step 3: Merge `update_value_map` into `flattened_row`
```python
merged_dict = {
    "user_id": 123,
    "profile.name": "John Doe",
    "profile.email": "REDACTED",  # From update_value_map
    "profile.preferences.theme": "dark",
    "profile.preferences.notifications": None,  # From update_value_map
    "profile.tags.0": None,  # From update_value_map
    "profile.tags.1": None,  # From update_value_map
    "profile.tags.2": None,  # From update_value_map
    "activity.last_login": "2023-05-15",
    "activity.login_count": 42
}
```

#### Step 4: Unflatten the merged dictionary
```python
nested_result = {
    "user_id": 123,
    "profile": {
        "name": "John Doe",
        "email": "REDACTED",
        "preferences": {
            "theme": "dark",
            "notifications": None
        },
        "tags": [None, None, None]  # Reconstructed from indexed entries
    },
    "activity": {
        "last_login": "2023-05-15",
        "login_count": 42
    }
}
```

#### Step 5: Replace arrays containing only `None` values with empty arrays
```python
nested_result_with_arrays_fixed = {
    "user_id": 123,
    "profile": {
        "name": "John Doe",
        "email": "REDACTED",
        "preferences": {
            "theme": "dark",
            "notifications": None
        },
        "tags": []  # Converted from [None, None, None] to empty array
    },
    "activity": {
        "last_login": "2023-05-15",
        "login_count": 42
    }
}
```

#### Step 6: Only keep top-level keys that are in the `update_value_map`
```python
# Top-level keys in update_value_map are "profile" only
top_level_keys = {"profile"}

final_update_map = {
    "profile": {
        "name": "John Doe",
        "email": "REDACTED",
        "preferences": {
            "theme": "dark",
            "notifications": null
        },
        "tags": []  # Empty array
    }
}
```

#### Step 7: Create SQL Update statements
This generates a SQLAlchemy Update object that would translate to:

```sql
UPDATE `project_id.dataset_id.table_name`
SET
  profile = {
    "name": "John Doe",
    "email": "REDACTED",
    "preferences": {
      "theme": "dark",
      "notifications": null
    },
    "tags": []
  }
WHERE user_id = 123
```

### Array Handling Notes

- Individual array elements can be targeted using indexed keys like `profile.tags.0`
- When all elements in an array become `None`, it's automatically converted to an empty array `[]`

This approach ensures that complex nested JSON structures in BigQuery can be properly updated while maintaining their hierarchical structure.
