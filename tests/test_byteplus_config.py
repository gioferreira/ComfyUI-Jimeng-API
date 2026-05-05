import os
import unittest
from unittest.mock import patch

from nodes.byteplus_config import (
    BYTEPLUS_BASE_URL,
    BytePlusConfigError,
    resolve_seedance2_model,
    get_api_key,
)


class BytePlusConfigTests(unittest.TestCase):
    def test_prefers_ark_api_key(self):
        with patch.dict(
            os.environ, {"ARK_API_KEY": " ark ", "BYTEPLUS_API_KEY": "byte"}, clear=True
        ):
            self.assertEqual(get_api_key(), "ark")

    def test_falls_back_to_byteplus_api_key(self):
        with patch.dict(os.environ, {"BYTEPLUS_API_KEY": " byte "}, clear=True):
            self.assertEqual(get_api_key(), "byte")

    def test_missing_key_raises_clear_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(BytePlusConfigError, "ARK_API_KEY"):
                get_api_key()

    def test_resolves_seedance2_model_ids(self):
        self.assertEqual(
            resolve_seedance2_model("Seedance 2.0"),
            "dreamina-seedance-2-0-260128",
        )
        self.assertEqual(
            resolve_seedance2_model("Seedance 2.0 Fast"),
            "dreamina-seedance-2-0-fast-260128",
        )

    def test_unknown_seedance2_model_raises_clear_error(self):
        with self.assertRaisesRegex(BytePlusConfigError, "Unknown Seedance 2.0 model"):
            resolve_seedance2_model("doubao-seedance-2-0")

    def test_base_url_points_to_byteplus_data_plane(self):
        self.assertEqual(
            BYTEPLUS_BASE_URL,
            "https://ark.ap-southeast.bytepluses.com/api/v3",
        )


if __name__ == "__main__":
    unittest.main()
