"""This module is responsible for parsing and verifying file, either with or without a server being available."""
from fidesctl.core.utils import echo_green
from fideslang import Taxonomy
from fideslang.manifests import ingest_manifests
from fideslang.parse import load_manifests_into_taxonomy


def parse(manifests_dir: str) -> Taxonomy:
    """
    Parse local manifest file(s) into a Taxonomy.
    """

    echo_green(f"Loading resource manifests from: {manifests_dir}")
    ingested_manifests = ingest_manifests(manifests_dir)
    taxonomy = load_manifests_into_taxonomy(ingested_manifests)
    echo_green("Taxonomy successfully created.")
    return taxonomy
