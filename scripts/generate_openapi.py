"""
Exports the OpenAPI JSON to a file, which can then be imported into the mkdocs site.

Usage:
  python generate_openapi.py [outfile_path]

  outfile_path: file path to write the output file to (defaults to "openapi.json")
"""
import json
import sys

from fidesops.main import app

if __name__ == "__main__":
    outfile_path = "openapi.json"

    if len(sys.argv) > 1:
        outfile_path = sys.argv[1]
    print(f"Generating OpenAPI JSON from fidesops and writing to '{outfile_path}'...")
    with open(outfile_path, "w") as outfile:
        json.dump(app.openapi(), outfile, indent=2)
        print(f"Exported OpenAPI JSON from fidesops to '{outfile_path}'")
