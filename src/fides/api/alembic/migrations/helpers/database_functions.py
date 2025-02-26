import uuid


def generate_record_id(prefix):
    """Generates an ID that can be used for a database table row ID."""
    return prefix + "_" + str(uuid.uuid4())
