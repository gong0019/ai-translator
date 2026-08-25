#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate and expand comprehensive 9-language specialist terminology catalogs.
Preserves all existing baseline terms and test fixtures.
"""

import json
import os
from pathlib import Path

SKILLS_DIR = Path("/home/gongchixin/www/qwen-translator/skills")

def merge_and_save_terms(filename, new_terms_list):
    filepath = SKILLS_DIR / filename
    existing_terms = []
    if filepath.exists():
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data.get("terms"), list):
                    existing_terms = data["terms"]
        except Exception:
            pass

    # Deduplicate by English key
    seen = set()
    merged = []
    for item in existing_terms:
        en_key = item.get("en", "").strip().lower()
        if en_key and en_key not in seen:
            seen.add(en_key)
            merged.append(item)

    for item in new_terms_list:
        en_key = item.get("en", "").strip().lower()
        if en_key and en_key not in seen:
            seen.add(en_key)
            merged.append(item)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump({"terms": merged}, f, ensure_ascii=False, indent=2)

    print(f"✓ {filename}: total {len(merged)} terms")

print("Building dictionaries...")
