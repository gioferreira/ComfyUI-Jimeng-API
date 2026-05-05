import pathlib
import unittest


NODES_VIDEO = pathlib.Path(__file__).resolve().parents[1] / "nodes" / "nodes_video.py"


class Seedance2RuntimeOptionsSourceTests(unittest.TestCase):
    def test_seedance2_omits_runtime_options_even_with_endpoint_id(self):
        source = NODES_VIDEO.read_text(encoding="utf-8")

        self.assertIn("node_class_type=\"JimengSeedance2\"", source)
        self.assertIn("service_tier=None", source)
        self.assertIn("execution_expires_after=None", source)


if __name__ == "__main__":
    unittest.main()
