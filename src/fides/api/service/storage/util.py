import os

LOCAL_FIDES_UPLOAD_DIRECTORY = "fides_uploads"


def get_local_filename(file_key: str) -> str:
    """Verifies that the local storage directory exists"""
    if not os.path.exists(LOCAL_FIDES_UPLOAD_DIRECTORY):
        os.makedirs(LOCAL_FIDES_UPLOAD_DIRECTORY)
    return f"{LOCAL_FIDES_UPLOAD_DIRECTORY}/{file_key}"
