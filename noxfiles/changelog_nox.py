"""Contains nox sessions for managing changelog fragments."""

import re
from pathlib import Path
from typing import Dict, List, Optional

import nox

# Valid changelog types in order
CHANGELOG_TYPES = [
    "Added",
    "Changed",
    "Developer Experience",
    "Deprecated",
    "Docs",
    "Fixed",
    "Removed",
    "Security",
]

# Label URLs mapping
LABEL_URLS = {
    "high-risk": "https://github.com/ethyca/fides/labels/high-risk",
    "db-migration": "https://github.com/ethyca/fides/labels/db-migration",
}

CHANGELOG_DIR = Path("changelog")
CHANGELOG_FILE = Path("CHANGELOG.md")
TEMPLATE_FILE_NAME = "TEMPLATE.yaml"
GITHUB_REPO = "https://github.com/ethyca/fides"


class ChangelogEntry:
    """Represents a single changelog entry from a YAML fragment."""

    def __init__(
        self,
        entry_type: str,
        description: str,
        pr: Optional[int] = None,
        labels: Optional[List[str]] = None,
    ):
        self.type = entry_type
        self.description = description
        self.pr = pr
        self.labels = labels or []

    def to_markdown(self) -> str:
        """Convert entry to markdown format."""
        entry = f"- {self.description}"
        if self.pr:
            entry += f" [#{self.pr}]({GITHUB_REPO}/pull/{self.pr})"
        for label in self.labels:
            if label in LABEL_URLS:
                entry += f" {LABEL_URLS[label]}"
        return entry


def load_fragments() -> List[tuple[Path, ChangelogEntry]]:
    """Load all changelog fragment files and return list of (path, entry) tuples."""
    import yaml  # Import here since it's installed by the nox session

    if not CHANGELOG_DIR.exists():
        return []

    entries = []
    errors = []
    # Look for both .yaml and .yml files
    yaml_files = list(CHANGELOG_DIR.glob("*.yaml")) + list(CHANGELOG_DIR.glob("*.yml"))
    for yaml_file in yaml_files:
        if yaml_file.name == TEMPLATE_FILE_NAME:
            continue

        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                continue

            # Validate required fields
            missing = []
            if "type" not in data:
                missing.append("type")
            if "description" not in data:
                missing.append("description")
            if "pr" not in data:
                missing.append("pr")

            if missing:
                errors.append(
                    f"Missing required fields in {yaml_file.name}: {', '.join(missing)}"
                )
                continue

            entry_type = data["type"]
            if entry_type not in CHANGELOG_TYPES:
                errors.append(
                    f"Invalid type '{entry_type}' in {yaml_file.name}. "
                    f"Must be one of: {', '.join(CHANGELOG_TYPES)}"
                )
                continue

            entry = ChangelogEntry(
                entry_type=entry_type,
                description=data["description"],
                pr=data.get("pr"),
                labels=data.get("labels", []),
            )
            entries.append((yaml_file, entry))
        except Exception as e:
            errors.append(f"Error parsing {yaml_file.name}: {e}")

    if errors:
        error_msg = "Found errors in changelog fragments:\n" + "\n".join(
            f"  - {err}" for err in errors
        )
        raise ValueError(error_msg)

    return entries


def group_entries_by_type(
    entries: List[ChangelogEntry],
) -> Dict[str, List[ChangelogEntry]]:
    """Group entries by their type."""
    grouped = {entry_type: [] for entry_type in CHANGELOG_TYPES}
    for entry in entries:
        grouped[entry.type].append(entry)
    return grouped


def generate_changelog_section(grouped_entries: Dict[str, List[ChangelogEntry]]) -> str:
    """Generate markdown section for changelog entries."""
    lines = []
    for entry_type in CHANGELOG_TYPES:
        entries = grouped_entries[entry_type]
        if entries:
            lines.append(f"### {entry_type}")
            for entry in entries:
                lines.append(entry.to_markdown())
            lines.append("")  # Empty line after section

    return "\n".join(lines).rstrip()


def find_unreleased_section(content: str) -> tuple[int, int]:
    """Find the start and end line numbers of the Unreleased section."""
    lines = content.split("\n")
    start_idx = None
    end_idx = None

    for i, line in enumerate(lines):
        if line.startswith("## [Unreleased]"):
            start_idx = i
        elif start_idx is not None and line.startswith("## ["):
            # Found next release section
            end_idx = i
            break

    if start_idx is None:
        raise ValueError("Could not find [Unreleased] section in CHANGELOG.md")

    if end_idx is None:
        end_idx = len(lines)

    return start_idx, end_idx


def insert_entries_into_changelog(content: str, new_entries: str) -> str:
    """Insert new entries into the Unreleased section of CHANGELOG.md."""
    lines = content.split("\n")
    _, end_idx = find_unreleased_section(content)

    # Insert new entries at the end of the Unreleased section (before the next release section)
    # If there's existing content, add a blank line separator
    new_lines = lines[:end_idx]
    if new_lines and new_lines[-1].strip() != "":
        new_lines.append("")
    new_lines.extend(new_entries.split("\n"))
    if new_lines[-1] != "":
        new_lines.append("")
    new_lines.extend(lines[end_idx:])

    return "\n".join(new_lines)


def finalize_release(content: str, version: str) -> str:
    """Create a new version section from Unreleased content and leave Unreleased empty."""
    lines = content.split("\n")

    # Find Unreleased section boundaries
    unreleased_start = None
    unreleased_end = None
    prev_version = None

    for i, line in enumerate(lines):
        if line.startswith("## [Unreleased]"):
            unreleased_start = i
            # Find the end of Unreleased section (next release section)
            for j in range(i + 1, len(lines)):
                if lines[j].startswith("## ["):
                    unreleased_end = j
                    # Extract version from next release line for compare link
                    match = re.search(r"## \[([\d.]+)\]", lines[j])
                    if match:
                        prev_version = match.group(1)
                    break
            if unreleased_end is None:
                unreleased_end = len(lines)
            break

    if unreleased_start is None:
        raise ValueError("Could not find [Unreleased] section in CHANGELOG.md")

    if prev_version is None:
        raise ValueError("Could not find previous version for compare link")

    # Extract Unreleased content (skip the header line)
    unreleased_content = lines[unreleased_start + 1 : unreleased_end]
    # Remove leading empty lines
    while unreleased_content and unreleased_content[0].strip() == "":
        unreleased_content = unreleased_content[1:]
    # Remove trailing empty lines
    while unreleased_content and unreleased_content[-1].strip() == "":
        unreleased_content = unreleased_content[:-1]

    # Build new content:
    # 1. Everything before Unreleased section
    # 2. Empty Unreleased section header
    # 3. New version section with the extracted content
    # 4. Everything after Unreleased section

    new_lines = lines[:unreleased_start]
    # Add empty Unreleased section
    new_lines.append(f"## [Unreleased]({GITHUB_REPO}/compare/{version}..main)")
    new_lines.append("")
    # Add new version section with the content
    new_lines.append(f"## [{version}]({GITHUB_REPO}/compare/{prev_version}..{version})")
    if unreleased_content:
        new_lines.append("")
        new_lines.extend(unreleased_content)
    new_lines.append("")
    # Add everything after Unreleased section
    new_lines.extend(lines[unreleased_end:])

    return "\n".join(new_lines)


@nox.session()
@nox.parametrize(
    "action",
    [
        nox.param("dry", id="dry"),
        nox.param("write", id="write"),
    ],
)
def changelog(  # pylint: disable=too-many-branches,too-many-statements
    session: nox.Session, action: str
) -> None:
    """
    Compile changelog fragments into CHANGELOG.md.

    Parameters:
        - changelog(dry) = Preview the changelog that would be generated without making changes
        - changelog(dry) -- --release VERSION = Preview with release finalization
        - changelog(dry) -- --prs PR1,PR2,PR3 = Preview with PR filtering
        - changelog(write) -- --release VERSION = Compile fragments and create new version section (--release required)
        - changelog(write) -- --release VERSION --prs PR1,PR2,PR3 = Only include specific PRs (for patch releases)
    """
    session.install("pyyaml")

    # Check for release flag
    release_version = None
    if "--release" in session.posargs:
        release_idx = session.posargs.index("--release")
        if release_idx + 1 < len(session.posargs):
            release_version = session.posargs[release_idx + 1]
        else:
            session.error("--release flag requires a version number")

    # Require --release for write action
    if action == "write" and not release_version:
        session.error(
            "changelog(write) requires --release VERSION flag (e.g., --release 2.77.0)"
        )

    # Check for PR filter flag (for patch releases)
    pr_filter = None
    if "--prs" in session.posargs:
        pr_idx = session.posargs.index("--prs")
        if pr_idx + 1 < len(session.posargs):
            pr_list_str = session.posargs[pr_idx + 1]
            try:
                pr_filter = [int(pr.strip()) for pr in pr_list_str.split(",")]
            except ValueError:
                session.error(
                    "--prs flag requires a comma-separated list of PR numbers (e.g., --prs 1234,5678)"
                )
        else:
            session.error("--prs flag requires a comma-separated list of PR numbers")

    # Load fragments
    try:
        all_fragment_data = load_fragments()
    except ValueError as e:
        session.error(str(e))

    if not all_fragment_data:
        session.log("No changelog fragments found in changelog/ directory")
        return

    # Filter by PR numbers if specified
    fragment_data = all_fragment_data
    if pr_filter:
        filtered_data = []
        for path, entry in all_fragment_data:
            if entry.pr and entry.pr in pr_filter:
                filtered_data.append((path, entry))
            elif not entry.pr:
                session.warn(
                    f"Fragment {path.name} has no PR number and will be skipped (--prs filter active)"
                )

        if not filtered_data:
            session.error(
                f"No fragments found matching PR numbers: {', '.join(map(str, pr_filter))}"
            )

        fragment_data = filtered_data
        session.log(
            f"Filtering to {len(fragment_data)} fragment(s) matching PR numbers: {', '.join(map(str, pr_filter))}"
        )

    fragment_paths, entries = zip(*fragment_data) if fragment_data else ([], [])

    # Get all fragment paths for comparison (when using --prs)
    all_fragment_paths = {path for path, _ in all_fragment_data} if pr_filter else set()

    # Validate all entries have valid types (double-check)
    invalid_entries = [
        (path, entry)
        for path, entry in fragment_data
        if entry.type not in CHANGELOG_TYPES
    ]
    if invalid_entries:
        error_msg = "Found entries with invalid types:\n"
        for path, entry in invalid_entries:
            error_msg += f"  - {path.name}: type '{entry.type}' is not valid. Must be one of: {', '.join(CHANGELOG_TYPES)}\n"
        session.error(error_msg)

    grouped = group_entries_by_type(list(entries))
    new_section = generate_changelog_section(grouped)

    if action == "dry":
        session.log("=" * 60)
        session.log("DRY RUN - No changes will be made")
        session.log("=" * 60)
        session.log(f"\nFound {len(entries)} changelog fragment(s):")
        for path in fragment_paths:
            session.log(f"  - {path}")
        if pr_filter:
            session.log(f"\nFiltered to PRs: {', '.join(map(str, pr_filter))}")
        session.log("\nGenerated changelog section:")
        session.log("-" * 60)
        print(new_section)
        session.log("-" * 60)
        session.log(f"\nFiles that would be deleted: {len(fragment_paths)}")
        if pr_filter:
            # Show which files would remain
            remaining = [f for f in all_fragment_paths if f not in fragment_paths]
            if remaining:
                session.log(f"Files that would remain in changelog/: {len(remaining)}")
                for f in remaining:
                    session.log(f"  - {f.name}")
        if release_version:
            session.log(f"Would finalize release as version: {release_version}")

    elif action == "write":
        # Read current CHANGELOG.md
        if not CHANGELOG_FILE.exists():
            session.error(f"{CHANGELOG_FILE} does not exist")

        with open(CHANGELOG_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        # Insert new entries
        try:
            updated_content = insert_entries_into_changelog(content, new_section)
        except ValueError as e:
            session.error(str(e))

        # Finalize release if requested
        if release_version:
            try:
                updated_content = finalize_release(updated_content, release_version)
                session.log(f"Finalized release as version {release_version}")
            except ValueError as e:
                session.error(str(e))

        # Write updated CHANGELOG.md
        with open(CHANGELOG_FILE, "w", encoding="utf-8") as f:
            f.write(updated_content)
        session.log(f"Updated {CHANGELOG_FILE}")

        # Delete fragment files (only the ones that were processed)
        for fragment_path in fragment_paths:
            fragment_path.unlink()
            session.log(f"Deleted {fragment_path}")

        # Show remaining files if using PR filter
        if pr_filter:
            remaining = [f for f in all_fragment_paths if f not in fragment_paths]
            if remaining:
                session.log(
                    f"\nRemaining fragments in changelog/ (not included in this release): {len(remaining)}"
                )
                for f in remaining:
                    session.log(f"  - {f.name}")

        session.log(f"Successfully compiled {len(entries)} changelog entries")

    else:
        session.error(f"Invalid action: {action}")
