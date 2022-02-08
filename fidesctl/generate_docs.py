"""
This module handles generating documentation from code.
"""
import json
import sys

from fidesapi.main import app
from fidesctl.core.config import get_config


def generate_openapi(outfile_dir: str) -> None:
    "Write out an openapi.json file for the API."

    outfile_name = "api/openapi.json"
    outfile_path = f"{outfile_dir}/{outfile_name}"
    print(f"Generating OpenAPI JSON from fidesapi and writing to '{outfile_path}'...")
    with open(outfile_path, "w") as outfile:
        json.dump(app.openapi(), outfile, indent=2)
        print(f"Exported OpenAPI JSON from fidesapi to '{outfile_path}'")


def generate_config_docs(outfile_dir: str) -> None:
    "Write out a json schema for the fidesctl config."

    outfile_name = "installation/config_schema.json"
    outfile_path = f"{outfile_dir}/{outfile_name}"
    print(f"Generating Config JSON Schema and writing to '{outfile_path}'...")
    with open(outfile_path, "w") as outfile:
        config_schema = get_config().schema_json(indent=2)
        outfile.write(config_schema)
        print(f"Exported Config JSON Schema '{outfile_path}'")


if __name__ == "__main__":
    outfile_dir = sys.argv[1]
    generate_openapi(outfile_dir)
    generate_config_docs(outfile_dir)
