import pathlib
import unittest


NODES_VIDEO = pathlib.Path(__file__).resolve().parents[1] / "nodes" / "nodes_video.py"


class Seedance2EndpointOverrideSourceTests(unittest.TestCase):
    def test_seedance2_exposes_endpoint_override_input(self):
        source = NODES_VIDEO.read_text(encoding="utf-8")

        self.assertIn("comfy_io.String.Input(", source)
        self.assertIn('"endpoint_id",', source)
        self.assertIn("endpoint_id,", source)

    def test_seedance2_uses_endpoint_override_as_model_name(self):
        source = NODES_VIDEO.read_text(encoding="utf-8")

        self.assertIn("model_name = (endpoint_id or \"\").strip() or resolve_model_id(model_version)", source)
        self.assertIn("model_name=model_name", source)


if __name__ == "__main__":
    unittest.main()
