"""This module is responsible for parsing and verifying file, either with or without a server being available."""

from fideslang.manifests import ingest_manifests
from fideslang.models import Taxonomy
from fideslang.parse import load_manifests_into_taxonomy

from fides.common.utils import echo_green
from fides.core.utils import get_manifest_list


def parse(manifests_dir: str) -> Taxonomy:
    """
    Parse local manifest file(s) into a Taxonomy.
    """

    # Check if any manifests exist before trying to parse them
    print(f"Loading resource manifests from: {manifests_dir}")
    if not get_manifest_list(manifests_dir):
        print("No manifests found to parse, skipping...")
        return Taxonomy()
    ingested_manifests = ingest_manifests(manifests_dir)
    taxonomy = load_manifests_into_taxonomy(ingested_manifests)
    echo_green("Taxonomy successfully created.")
    return taxonomy
