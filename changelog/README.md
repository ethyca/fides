# Changelog Fragments

This directory contains changelog entry fragments that are compiled into `CHANGELOG.md` during releases.

## Creating an Entry

1. Copy `TEMPLATE.yaml` to a new file (use `.yaml` or `.yml` extension)
2. Name it using your PR number (e.g., `1234.yaml`) or a descriptive slug (e.g., `add-feature-name.yaml`)
3. Fill in the required fields:
   - `type`: One of: Added, Changed, Developer Experience, Deprecated, Docs, Fixed, Removed, Security
   - `description`: Short description (start with past-tense verb, e.g., "Added...", "Fixed...")
   - `pr`: PR number
   - `labels`: Optional list: `["high-risk"]`, `["db-migration"]`, or both

## Compiling Entries

**Preview (dry run):**
```sh
nox -s "changelog(dry)" -- --release 2.77.0
```

**Compile and create release section:**
```sh
nox -s "changelog(write)" -- --release 2.77.0
```

**For patch releases (only specific PRs):**
```sh
nox -s "changelog(write)" -- --release 2.76.2 --prs 1234,5678
```

The script will:
- Compile fragments into a new version section
- Delete processed fragment files
- Update compare links in `CHANGELOG.md`

**Note:** The `write` action always requires the `--release VERSION` flag.
