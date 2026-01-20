#!/usr/bin/env python3
"""
Generate OpenAPI schema from the Fides FastAPI application.

This script generates the OpenAPI schema without needing to start the server,
making it much faster for CI/CD pipelines.

Usage:
    python scripts/generate_openapi_schema.py [output_file]

Default output: openapi.json
"""

import json
import sys
from pathlib import Path


def generate_openapi_schema(output_path: str = "openapi.json") -> str:
    """
    Generate OpenAPI schema from the FastAPI app.

    Args:
        output_path: Path where the schema JSON should be written

    Returns:
        Path to the generated schema file
    """
    print(f"Generating OpenAPI schema...")

    # Import the FastAPI app
    # Note: This import will trigger app initialization
    from fides.api.main import app

    # Generate the OpenAPI schema
    schema = app.openapi()

    # Write to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(schema, f, indent=2)

    print(f"✅ OpenAPI schema written to: {output_file}")
    print(f"   Schemas: {len(schema.get('components', {}).get('schemas', {}))}")
    print(f"   Paths: {len(schema.get('paths', {}))}")

    return str(output_file)


if __name__ == "__main__":
    output_path = sys.argv[1] if len(sys.argv) > 1 else "openapi.json"
    try:
        generate_openapi_schema(output_path)
    except Exception as e:
        print(f"❌ Error generating OpenAPI schema: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
