import unittest

from nodes.byteplus_payloads import (
    BytePlusPayloadError,
    build_seedance2_task_kwargs,
    compact_payload_for_log,
)


class BytePlusPayloadTests(unittest.TestCase):
    def test_builds_first_last_frame_payload(self):
        payload = build_seedance2_task_kwargs(
            model="dreamina-seedance-2-0-260128",
            prompt="make it move",
            first_frame_data_url="data:image/png;base64,first",
            last_frame_data_url="data:image/png;base64,last",
            reference_image_data_urls=[],
            resolution="720p",
            ratio="adaptive",
            duration=5,
            generate_audio=True,
            seed=123,
        )

        self.assertEqual(payload["model"], "dreamina-seedance-2-0-260128")
        self.assertEqual(payload["content"][0], {"type": "text", "text": "make it move"})
        self.assertEqual(payload["content"][1]["role"], "first_frame")
        self.assertEqual(payload["content"][2]["role"], "last_frame")
        self.assertEqual(payload["resolution"], "720p")
        self.assertEqual(payload["ratio"], "adaptive")
        self.assertEqual(payload["duration"], 5)
        self.assertTrue(payload["generate_audio"])
        self.assertEqual(payload["seed"], 123)

    def test_builds_reference_image_payload(self):
        payload = build_seedance2_task_kwargs(
            model="dreamina-seedance-2-0-fast-260128",
            prompt="use these refs",
            first_frame_data_url=None,
            last_frame_data_url=None,
            reference_image_data_urls=[
                "data:image/png;base64,one",
                "data:image/png;base64,two",
            ],
            resolution="720p",
            ratio="16:9",
            duration=5,
            generate_audio=False,
            seed=-1,
        )

        roles = [item["role"] for item in payload["content"][1:]]
        self.assertEqual(roles, ["reference_image", "reference_image"])
        self.assertNotIn("seed", payload)

    def test_uses_default_ratio_when_text_to_video_ratio_is_adaptive(self):
        payload = build_seedance2_task_kwargs(
            model="dreamina-seedance-2-0-260128",
            prompt="text only",
            first_frame_data_url=None,
            last_frame_data_url=None,
            reference_image_data_urls=[],
            resolution="720p",
            ratio="adaptive",
            duration=5,
            generate_audio=False,
            seed=None,
        )

        self.assertEqual(payload["ratio"], "16:9")

    def test_rejects_last_frame_without_first_frame(self):
        with self.assertRaisesRegex(BytePlusPayloadError, "first frame"):
            build_seedance2_task_kwargs(
                model="dreamina-seedance-2-0-260128",
                prompt="bad",
                first_frame_data_url=None,
                last_frame_data_url="data:image/png;base64,last",
                reference_image_data_urls=[],
                resolution="720p",
                ratio="adaptive",
                duration=5,
                generate_audio=False,
                seed=-1,
            )

    def test_rejects_mixed_flf_and_references(self):
        with self.assertRaisesRegex(BytePlusPayloadError, "cannot be mixed"):
            build_seedance2_task_kwargs(
                model="dreamina-seedance-2-0-260128",
                prompt="bad",
                first_frame_data_url="data:image/png;base64,first",
                last_frame_data_url=None,
                reference_image_data_urls=["data:image/png;base64,ref"],
                resolution="720p",
                ratio="adaptive",
                duration=5,
                generate_audio=False,
                seed=-1,
            )

    def test_requires_prompt_or_visual_input(self):
        with self.assertRaisesRegex(BytePlusPayloadError, "prompt or visual input"):
            build_seedance2_task_kwargs(
                model="dreamina-seedance-2-0-260128",
                prompt=" ",
                first_frame_data_url=None,
                last_frame_data_url=None,
                reference_image_data_urls=[],
                resolution="720p",
                ratio="16:9",
                duration=5,
                generate_audio=False,
                seed=-1,
            )

    def test_compact_payload_truncates_data_urls_for_logs(self):
        payload = {
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": "data:image/png;base64," + ("a" * 240)},
                    "role": "reference_image",
                }
            ]
        }

        compact = compact_payload_for_log(payload)

        self.assertIn("<truncated:", compact["content"][0]["image_url"]["url"])
        self.assertLess(len(compact["content"][0]["image_url"]["url"]), 180)


if __name__ == "__main__":
    unittest.main()
