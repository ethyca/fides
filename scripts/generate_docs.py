"""
This module handles generating documentation from code.
"""
import json
import sys

from fides.api.main import app
from fides.core.config import CONFIG
from fides.core.config.create import generate_config_docs


def generate_openapi(outfile_dir: str) -> str:
    "Write out an openapi.json file for the API."

    outfile_name = "api/openapi.json"
    outfile_path = f"{outfile_dir}/{outfile_name}"
    print(f"Generating OpenAPI JSON from the API and writing to '{outfile_path}'...")
    with open(outfile_path, "w") as outfile:
        json.dump(app.openapi(), outfile, indent=2)
        print(f"Exported OpenAPI JSON from the API to '{outfile_path}'")
    return outfile_path


if __name__ == "__main__":
    default_outfile_dir = "docs/fides/docs"
    try:
        outfile_dir = sys.argv[1]
    except IndexError:
        outfile_dir = default_outfile_dir

    generate_openapi(outfile_dir)
    generate_config_docs(
        config=CONFIG, outfile_path="docs/fides/docs/config/fides.toml"
    )
