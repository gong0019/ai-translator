#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate the multilingual terminology catalogs in this checkout."""

from term_catalog_utils import skills_directory, validate_catalog


def main():
    problems = []
    for path in sorted(skills_directory().glob("*_terms.json")):
        for problem in validate_catalog(path):
            problems.append(f"{path.name}: {problem}")
    if problems:
        raise SystemExit("\n".join(problems))
    print("✓ All terminology catalogs are complete and have unique source terms.")


if __name__ == "__main__":
    main()
