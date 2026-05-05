# BytePlus Seedance 2 Port Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a focused BytePlus ModelArk Seedance 2.0 ComfyUI integration for reference-to-video and first-frame/last-frame image-to-video.

**Architecture:** Keep the mature Jimeng video executor shape, but isolate BytePlus-specific configuration, model IDs, and payload construction in small modules. The first implementation should make request construction testable without live API calls, then wire that into a ComfyUI node.

**Tech Stack:** Python 3, ComfyUI custom nodes, Ark runtime SDK, `requests`, `torch`, `Pillow`, `unittest`.

---

## File Structure

- Create `nodes/byteplus_config.py`: API key resolution, base URL, model metadata.
- Create `nodes/byteplus_payloads.py`: pure helpers for Seedance 2.0 content and task kwargs.
- Create `nodes/byteplus_client.py`: BytePlus client wrapper and SDK import fallback.
- Create `nodes/byteplus_video.py`: ComfyUI node(s) for Seedance 2.0.
- Modify `__init__.py`: register the BytePlus node while keeping Jimeng nodes intact during the first pass.
- Modify `requirements.txt` and `pyproject.toml`: include the BytePlus Ark runtime dependency if needed.
- Create `tests/test_byteplus_config.py`.
- Create `tests/test_byteplus_payloads.py`.
- Create `tests/test_byteplus_node_schema.py` if ComfyUI imports can be stubbed safely.
- Update `README.md`: document API key setup and first-pass supported workflows.

## Task 1: BytePlus Config And Model IDs

**Files:**
- Create: `nodes/byteplus_config.py`
- Test: `tests/test_byteplus_config.py`

- [ ] **Step 1: Write failing tests for API key precedence**

```python
import os
import unittest
from unittest.mock import patch

from nodes.byteplus_config import BytePlusConfigError, get_api_key


class BytePlusConfigTests(unittest.TestCase):
    def test_prefers_ark_api_key(self):
        with patch.dict(os.environ, {"ARK_API_KEY": "ark", "BYTEPLUS_API_KEY": "byte"}, clear=True):
            self.assertEqual(get_api_key(), "ark")

    def test_falls_back_to_byteplus_api_key(self):
        with patch.dict(os.environ, {"BYTEPLUS_API_KEY": "byte"}, clear=True):
            self.assertEqual(get_api_key(), "byte")

    def test_missing_key_raises_clear_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(BytePlusConfigError):
                get_api_key()
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python3 -m unittest tests/test_byteplus_config.py -v`

Expected: FAIL because `nodes.byteplus_config` does not exist.

- [ ] **Step 3: Implement config module**

```python
import os

BYTEPLUS_BASE_URL = "https://ark.ap-southeast.bytepluses.com/api/v3"

SEEDANCE2_MODELS = {
    "Seedance 2.0": "dreamina-seedance-2-0-260128",
    "Seedance 2.0 Fast": "dreamina-seedance-2-0-fast-260128",
}


class BytePlusConfigError(RuntimeError):
    pass


def get_api_key():
    for name in ("ARK_API_KEY", "BYTEPLUS_API_KEY"):
        value = os.environ.get(name)
        if value and value.strip():
            return value.strip()
    raise BytePlusConfigError(
        "BytePlus API key not found. Set ARK_API_KEY or BYTEPLUS_API_KEY."
    )


def resolve_seedance2_model(display_name):
    try:
        return SEEDANCE2_MODELS[display_name]
    except KeyError as exc:
        raise BytePlusConfigError(f"Unknown Seedance 2.0 model: {display_name}") from exc
```

- [ ] **Step 4: Run tests**

Run: `python3 -m unittest tests/test_byteplus_config.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add nodes/byteplus_config.py tests/test_byteplus_config.py
git commit -m "feat: add byteplus modelark config"
```

## Task 2: Pure Seedance 2.0 Payload Builder

**Files:**
- Create: `nodes/byteplus_payloads.py`
- Test: `tests/test_byteplus_payloads.py`

- [ ] **Step 1: Write failing payload tests**

```python
import unittest

from nodes.byteplus_payloads import (
    BytePlusPayloadError,
    build_seedance2_task_kwargs,
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
        self.assertEqual(payload["content"][1]["role"], "first_frame")
        self.assertEqual(payload["content"][2]["role"], "last_frame")
        self.assertEqual(payload["resolution"], "720p")
        self.assertEqual(payload["duration"], 5)
        self.assertTrue(payload["generate_audio"])
        self.assertEqual(payload["seed"], 123)

    def test_builds_reference_image_payload(self):
        payload = build_seedance2_task_kwargs(
            model="dreamina-seedance-2-0-fast-260128",
            prompt="use these refs",
            first_frame_data_url=None,
            last_frame_data_url=None,
            reference_image_data_urls=["data:image/png;base64,one", "data:image/png;base64,two"],
            resolution="720p",
            ratio="16:9",
            duration=5,
            generate_audio=False,
            seed=-1,
        )

        roles = [item["role"] for item in payload["content"][1:]]
        self.assertEqual(roles, ["reference_image", "reference_image"])
        self.assertNotIn("seed", payload)

    def test_rejects_last_frame_without_first_frame(self):
        with self.assertRaises(BytePlusPayloadError):
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
        with self.assertRaises(BytePlusPayloadError):
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
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python3 -m unittest tests/test_byteplus_payloads.py -v`

Expected: FAIL because `nodes.byteplus_payloads` does not exist.

- [ ] **Step 3: Implement payload builder**

Create a pure helper that returns kwargs suitable for
`client.content_generation.tasks.create(**payload)`. It must:

- always include text content when prompt is non-empty
- add `first_frame` and optional `last_frame` roles for FLF2V
- add `reference_image` roles for reference-to-video
- reject mixed FLF2V and reference image inputs
- omit `seed` when seed is `-1` or `None`
- use `16:9` when no image/reference exists and ratio is `adaptive`

- [ ] **Step 4: Run tests**

Run: `python3 -m unittest tests/test_byteplus_payloads.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add nodes/byteplus_payloads.py tests/test_byteplus_payloads.py
git commit -m "feat: build byteplus seedance2 payloads"
```

## Task 3: BytePlus Client Wrapper

**Files:**
- Create: `nodes/byteplus_client.py`
- Test: `tests/test_byteplus_config.py`

- [ ] **Step 1: Add failing import/client tests**

Add tests that patch `nodes.byteplus_client.Ark` and assert `create_client()`
passes `api_key` and `base_url`.

- [ ] **Step 2: Run tests**

Run: `python3 -m unittest tests/test_byteplus_config.py -v`

Expected: FAIL because `byteplus_client` does not exist.

- [ ] **Step 3: Implement client wrapper**

Implementation rule:

- Prefer `byteplussdkarkruntime.Ark`.
- Fall back to `volcenginesdkarkruntime.Ark` if needed, since the existing
  Jimeng repo already depends on it.
- Construct with `base_url=BYTEPLUS_BASE_URL`.

- [ ] **Step 4: Run tests**

Run: `python3 -m unittest tests/test_byteplus_config.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add nodes/byteplus_client.py tests/test_byteplus_config.py
git commit -m "feat: create byteplus ark client wrapper"
```

## Task 4: Wire A Focused Seedance 2.0 Node

**Files:**
- Create: `nodes/byteplus_video.py`
- Modify: `__init__.py`
- Optional Modify: `nodes/utils_download.py` or reuse existing Jimeng helpers

- [ ] **Step 1: Add node class**

Create `BytePlusSeedance2Video` with inputs:

- API key optional string override, or a client input if we keep a client node
- model: `Seedance 2.0`, `Seedance 2.0 Fast`
- prompt
- first_frame_image optional
- last_frame_image optional
- reference_image_1 optional
- reference_image_2 optional
- reference_image_3 optional
- reference_image_4 optional
- resolution: `480p`, `720p`
- aspect_ratio: `16:9`, `4:3`, `1:1`, `3:4`, `9:16`, `21:9`, `adaptive`
- duration: 4-15
- generate_audio
- seed
- non_blocking
- filename_prefix

Outputs:

- `VIDEO`
- `IMAGE` last frame if available
- `STRING` response metadata

- [ ] **Step 2: Reuse existing image conversion**

Use Jimeng's existing tensor-to-data-url helper if it is small and local. If the
helper is too tangled, add a focused image conversion function in
`byteplus_payloads.py` and unit-test it separately.

- [ ] **Step 3: Submit and poll task**

Reuse Jimeng's executor if it accepts the BytePlus client and model IDs cleanly.
If it is too coupled, implement a minimal blocking polling path first:

```python
task = client.content_generation.tasks.create(**task_kwargs)
while status not in ("succeeded", "failed"):
    result = client.content_generation.tasks.get(task_id=task.id)
```

- [ ] **Step 4: Register node**

Update `__init__.py` to import and register the BytePlus node under a category
such as `BytePlus/Video`.

- [ ] **Step 5: Run import smoke test**

Run: `python3 -m py_compile __init__.py nodes/byteplus_video.py`

Expected: PASS. If local machine lacks ComfyUI modules, use targeted module
compilation for pure modules and document the ComfyUI import gap.

- [ ] **Step 6: Commit**

Run:

```bash
git add __init__.py nodes/byteplus_video.py
git commit -m "feat: add byteplus seedance2 video node"
```

## Task 5: Dependencies And Docs

**Files:**
- Modify: `requirements.txt`
- Modify: `pyproject.toml`
- Modify: `README.md`

- [ ] **Step 1: Update dependencies**

Add BytePlus SDK only if needed:

```text
byteplus-python-sdk-v2
```

or, if `byteplussdkarkruntime` is distributed separately:

```text
byteplussdkarkruntime
```

Verify the actual package name before committing. If the existing
`volcengine-python-sdk[ark]` works with the BytePlus base URL, keep dependency
changes minimal.

- [ ] **Step 2: Document setup**

Add README section:

- set `ARK_API_KEY` or `BYTEPLUS_API_KEY`
- activate the Seedance 2.0 model in BytePlus ModelArk
- use `dreamina-seedance-2-0-260128` / fast model
- supported first-pass workflows
- note that `ComfyUI-GFUtils` remains separate

- [ ] **Step 3: Run tests**

Run:

```bash
python3 -m unittest tests/test_byteplus_config.py tests/test_byteplus_payloads.py -v
python3 -m py_compile nodes/byteplus_config.py nodes/byteplus_payloads.py nodes/byteplus_client.py
```

Expected: PASS.

- [ ] **Step 4: Commit**

Run:

```bash
git add README.md requirements.txt pyproject.toml
git commit -m "docs: document byteplus seedance2 setup"
```

## Task 6: Manual ComfyUI Verification

**Files:**
- Optional Create: `example_workflows/BytePlus Seedance 2 FLF2V.json`
- Optional Create: `example_workflows/BytePlus Seedance 2 Reference Images.json`

- [ ] **Step 1: Install/update deps in the target ComfyUI environment**

Run from the custom node directory:

```bash
pip install -r requirements.txt
```

- [ ] **Step 2: Start ComfyUI**

Use the user's normal ComfyUI launch command.

- [ ] **Step 3: Verify node import**

Expected: Node appears under `BytePlus/Video`.

- [ ] **Step 4: Test FLF2V**

Use two small input images, `duration=4`, `resolution=480p`, audio disabled if
possible.

Expected: video output is produced, response metadata includes task ID and model.

- [ ] **Step 5: Test reference-to-video**

Use one or two reference images, `duration=4`, `resolution=480p`.

Expected: video output is produced, no conflict with FLF2V validation.

- [ ] **Step 6: Commit example workflows if useful**

Run:

```bash
git add example_workflows
git commit -m "docs: add byteplus seedance2 example workflows"
```
