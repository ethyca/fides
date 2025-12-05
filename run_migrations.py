#!/usr/bin/env python3
"""Run Fides database migrations against localhost database."""
import os
import sys
from pathlib import Path

# Override database settings via environment variables
os.environ["FIDES__DATABASE__SERVER"] = "localhost"
os.environ["FIDES__DATABASE__USER"] = "postgres"
os.environ["FIDES__DATABASE__PASSWORD"] = "fides"
os.environ["FIDES__DATABASE__PORT"] = "5432"
os.environ["FIDES__DATABASE__DB"] = "fides"

# Add src to path so we use local source code
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fides.api.db.database import migrate_db
from fides.config import get_config

# Get config (will use environment variables we set above)
config = get_config()
database_url = config.database.sync_database_uri

print(f"Running migrations against: {database_url}")
migrate_db(database_url)
print("Migrations completed successfully!")
