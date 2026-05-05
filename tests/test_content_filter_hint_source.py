import pathlib
import unittest


CONSTANTS = pathlib.Path(__file__).resolve().parents[1] / "nodes" / "constants.py"


class ContentFilterHintSourceTests(unittest.TestCase):
    def test_real_person_filter_error_mentions_readme_and_endpoint_id(self):
        source = CONSTANTS.read_text(encoding="utf-8")

        self.assertIn("InputMediaMayContainRealPerson", source)
        self.assertIn("See README.md", source)
        self.assertIn("Content Pre-filter", source)
        self.assertIn("endpoint_id", source)
        self.assertIn("ep-...", source)

    def test_real_person_filter_text_match_handles_combined_image_or_video_message(self):
        source = CONSTANTS.read_text(encoding="utf-8")

        self.assertIn(
            '"input image or video may contain a real person": "InputMediaMayContainRealPerson"',
            source,
        )


if __name__ == "__main__":
    unittest.main()
