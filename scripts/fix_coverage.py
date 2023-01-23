"""
This module is a workaround to create a valid `.lcov` file to be
used by Code Climate.

Usage:
  python scripts/fix_coverage.py <test_group>

Example:
  input: python scripts/fix_coverage.py lib
  output: coverage/lib-fixed.lcov

https://github.com/ethyca/fides/pull/2198
"""
import sys


def write_fixed_file(test_group: str) -> None:
    """Replace the default 'installation' path with the relative source path."""
    path_to_replace = "/usr/local/lib/python{}/site-packages/"
    with open(f"coverage/{test_group}.lcov", "r", encoding="utf-8") as lcov_file:
        coverage_file = lcov_file.read()

        # Replace all possible versions of Python we test
        fixed_file = (
            coverage_file.replace(path_to_replace.format("3.10"), "src/")
            .replace(path_to_replace.format("3.9"), "src/")
            .replace(path_to_replace.format("3.8"), "src/")
        )

    with open(f"coverage/{test_group}-fixed.lcov", "w", encoding="utf-8") as lcov_file:
        lcov_file.write(fixed_file)


if __name__ == "__main__":
    test_group = sys.argv[1]
    write_fixed_file(test_group)
