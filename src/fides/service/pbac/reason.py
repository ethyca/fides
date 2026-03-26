"""Human-readable violation reason generation.

This module has ZERO external dependencies.
"""

from __future__ import annotations

from fides.service.pbac.types import Violation


def generate_violation_reason(violation: Violation) -> str:
    """Produce a detailed, human-readable explanation of a violation."""
    parts: list[str] = []

    parts.append(
        f"Consumer '{violation.consumer_name}' (ID: {violation.consumer_id}) "
        f"accessed dataset '{violation.dataset_key}'"
    )

    if violation.collection:
        parts.append(f", collection '{violation.collection}'")

    parts.append(".\n\n")

    if not violation.consumer_purposes:
        parts.append(
            "The consumer has no declared data purposes. All dataset accesses "
            "are violations until purposes are assigned to this consumer."
        )
    else:
        consumer_list = ", ".join(sorted(violation.consumer_purposes))
        dataset_list = ", ".join(sorted(violation.dataset_purposes))

        parts.append(f"Consumer's declared purposes: {consumer_list}\n")
        parts.append(f"Dataset's allowed purposes: {dataset_list}\n\n")
        parts.append(
            "None of the consumer's declared purposes match any of the "
            "dataset's allowed purposes. The consumer is not authorized "
            "to access this data under its current purpose assignments."
        )

    return "".join(parts)
