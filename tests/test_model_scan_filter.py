import os
import tempfile
import unittest
from unittest.mock import patch

import translator_cli


class ModelScanFilterTests(unittest.TestCase):
    def test_incomplete_download_metadata_hides_partial_model(self):
        with tempfile.TemporaryDirectory() as directory:
            completed_model = os.path.join(directory, "completed.gguf")
            downloading_model = os.path.join(directory, "downloading.gguf")
            open(completed_model, "wb").close()
            open(downloading_model, "wb").close()
            open(f"{downloading_model}.download-meta.json", "w", encoding="utf-8").close()

            cli = object.__new__(translator_cli.TranslatorCLI)
            cli.models_map = {}
            cli.config = {}
            cli.active_model_idx = "1"
            with patch.object(translator_cli, "MODELS_DIR", directory):
                cli.refresh_available_models()

            self.assertEqual(
                [info["filename"] for info in cli.models_map.values()],
                ["completed.gguf"],
            )


if __name__ == "__main__":
    unittest.main()
