import pathlib
import re
import unittest


UTILS_DOWNLOAD = pathlib.Path(__file__).resolve().parents[1] / "nodes" / "utils_download.py"


class UtilsDownloadSourceTests(unittest.TestCase):
    def test_video_download_has_longer_timeout_than_generic_download(self):
        source = UTILS_DOWNLOAD.read_text(encoding="utf-8")

        generic = int(re.search(r"DEFAULT_DOWNLOAD_TIMEOUT = (\d+)", source).group(1))
        video = int(re.search(r"DEFAULT_VIDEO_DOWNLOAD_TIMEOUT = (\d+)", source).group(1))

        self.assertGreater(video, generic)
        self.assertIn("timeout=DEFAULT_VIDEO_DOWNLOAD_TIMEOUT", source)

    def test_download_retry_logs_exception_type_for_empty_messages(self):
        source = UTILS_DOWNLOAD.read_text(encoding="utf-8")

        self.assertIn("def _format_download_error", source)
        self.assertIn("type(e).__name__", source)


if __name__ == "__main__":
    unittest.main()
