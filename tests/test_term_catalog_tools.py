import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).parent.parent
REQUIRED_LANGUAGES = ("en", "zh", "ja", "ko", "de", "fr", "es", "ru", "it")


def record(en, zh):
    return {
        "en": en,
        "zh": zh,
        "ja": en,
        "ko": en,
        "de": en,
        "fr": en,
        "es": en,
        "ru": en,
        "it": en,
    }


class TermCatalogToolTests(unittest.TestCase):
    def test_merge_preserves_existing_terms_and_ignores_duplicate_english_keys(self):
        from scripts.term_catalog_utils import merge_records

        merged = merge_records(
            [record("existing term", "已有词条")],
            [
                record("existing term", "不应覆盖"),
                record("new term", "新增词条"),
            ],
        )

        self.assertEqual(
            [(item["en"], item["zh"]) for item in merged],
            [("existing term", "已有词条"), ("new term", "新增词条")],
        )

    def test_catalog_validator_rejects_missing_language_and_duplicate_source(self):
        from scripts.term_catalog_utils import validate_records

        invalid = [record("duplicate", "重复"), record("duplicate", "重复二")]
        invalid[1].pop("it")

        problems = validate_records(invalid, REQUIRED_LANGUAGES)

        self.assertIn("duplicate source term: duplicate", problems)
        self.assertIn("record 2 missing language: it", problems)

    def test_build_all_terms_preserves_existing_catalog_content_in_an_isolated_checkout(self):
        self._run_builder_and_assert_preserved(
            "build_all_terms.py", "finance_terms.json", "SWIFT"
        )

    def test_full_database_builder_uses_the_checkout_skills_directory(self):
        self._run_builder_and_assert_preserved(
            "build_full_database.py", "finance_terms.json", "forex"
        )

    def test_trade_builder_uses_the_checkout_skills_directory(self):
        self._run_builder_and_assert_preserved(
            "populate_all_dictionaries.py", "trade_terms.json", "clean bill of lading"
        )

    def _run_builder_and_assert_preserved(self, builder_name, catalog_name, added_term):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            scripts_dir = root / "scripts"
            skills_dir = root / "skills"
            scripts_dir.mkdir()
            skills_dir.mkdir()
            shutil.copy2(PROJECT_ROOT / "scripts" / builder_name, scripts_dir / builder_name)
            shutil.copy2(
                PROJECT_ROOT / "scripts" / "term_catalog_utils.py",
                scripts_dir / "term_catalog_utils.py",
            )
            (skills_dir / catalog_name).write_text(
                json.dumps({"terms": [record("existing term", "已有词条")]}, ensure_ascii=False),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(scripts_dir / builder_name)],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            terms = json.loads((skills_dir / catalog_name).read_text(encoding="utf-8"))["terms"]
            source_terms = [item["en"] for item in terms]
            self.assertIn("existing term", source_terms)
            self.assertIn(added_term, source_terms)


if __name__ == "__main__":
    unittest.main()
