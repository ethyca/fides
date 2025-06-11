from fides.api.schemas.manual_tasks.manual_task_config import ManualTaskFieldType

# Shared test data
CONFIG_TYPE = "access_privacy_request"
FIELDS = [
    {
        "field_key": "field1",
        "field_type": ManualTaskFieldType.text,
        "field_metadata": {
            "label": "Field 1",
            "required": True,
            "help_text": "This is field 1",
            "placeholder": "Enter text here",
        },
    },
    {
        "field_key": "field2",
        "field_type": ManualTaskFieldType.text,
        "field_metadata": {
            "label": "Field 2",
            "required": False,
            "help_text": "This is field 2",
        },
    },
]
