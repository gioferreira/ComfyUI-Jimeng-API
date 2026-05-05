# BytePlus Seedance 2 Port Design

## Decision

Build this as a clean BytePlus-focused fork of `ComfyUI-Jimeng-API`, not inside
`ComfyUI-GFUtils`.

`ComfyUI-GFUtils` should stay a lightweight personal utility node set. A
ModelArk integration has a separate lifecycle: API keys, remote costs, model
activation, SDK/API compatibility, polling, video downloads, and provider docs.
Keeping it separate makes installation safer and makes future upstream syncs
from Jimeng easier.

## Goal

Port the useful Jimeng Seedance 2.0 video workflow to BytePlus ModelArk, with
first priority on:

- reference-to-video using one or more reference images
- first-frame / last-frame image-to-video

The first deliverable should be usable in ComfyUI with a BytePlus API key and
should not require Comfy Partner Nodes or Comfy credits.

## Source Material

- `ComfyUI-Jimeng-API`: mature ComfyUI integration with Seedance 2.0 UI,
  content construction, polling, local video output, last-frame output, quota
  controls, and non-blocking task cache.
- `ComfyUI-Seed-API`: confirms the BytePlus data-plane base URL and simple
  HTTP flow, but its implementation is less complete.
- `modelark_seedance2.0_quickstart_package`: official BytePlus SDK example for
  Seedance 2.0 and the `dreamina-seedance-2-0-260128` model ID.
- BytePlus docs: data-plane base URL is
  `https://ark.ap-southeast.bytepluses.com/api/v3`, authenticated with
  `Authorization: Bearer $ARK_API_KEY`.

## Scope

### In Scope

- Rename/reframe the fork as a BytePlus ModelArk node set.
- Support API key loading from `ARK_API_KEY`, then `BYTEPLUS_API_KEY`, then
  optional local config.
- Use the BytePlus ModelArk data-plane base URL by default.
- Map Seedance 2.0 UI choices to BytePlus model IDs:
  - `dreamina-seedance-2-0-260128`
  - `dreamina-seedance-2-0-fast-260128`
- Implement or port a focused Seedance 2.0 node that supports:
  - text prompt
  - `first_frame_image`
  - `last_frame_image`
  - reference images
  - resolution
  - aspect ratio
  - duration / auto duration if accepted by the API
  - optional audio generation
  - seed when supported
  - blocking and non-blocking task behavior if the existing Jimeng executor can
    be retained safely
- Preserve useful outputs:
  - generated video
  - last frame when returned or extractable
  - JSON response/debug metadata
- Add unit tests around request construction and model mapping without calling
  the live API.
- Add a dry-run style test seam so API payloads can be validated without
  spending BytePlus credits.

### Out of Scope For First Pass

- Seedream image generation.
- Seedance 1.0 / 1.5 nodes.
- Visual understanding / Responses API nodes.
- Comfy Partner Node integration.
- Uploading local reference videos or audio unless it is already reliable after
  the minimal port.
- Full package publishing metadata cleanup beyond what ComfyUI needs to load the
  node.

## Architecture

Keep Jimeng's mature executor and ComfyUI integration patterns where possible,
but isolate provider-specific choices in a small BytePlus layer.

Proposed modules:

- `nodes/byteplus_config.py`: base URL, API key resolution, model IDs, and
  optional config file loading.
- `nodes/byteplus_client.py`: creates the Ark client and centralizes any SDK
  import differences between `volcenginesdkarkruntime` and
  `byteplussdkarkruntime`.
- `nodes/byteplus_video.py`: focused Seedance 2.0 ComfyUI node(s), adapted from
  Jimeng's `JimengSeedance2`.
- Existing Jimeng helpers can remain initially, but the public node names and
  categories should become BytePlus-oriented.

The first implementation should avoid broad rewrites. The safest route is to
copy/adapt the existing Seedance 2.0 path, then prune unrelated nodes after the
target workflow works.

## Data Flow

1. User adds a BytePlus client node or relies on environment variables.
2. Client resolves API key from `ARK_API_KEY`, `BYTEPLUS_API_KEY`, or local
   config.
3. Seedance 2.0 node converts ComfyUI images to data URLs.
4. Node builds `content`:
   - FLF2V: prompt, first frame with role `first_frame`, optional last frame
     with role `last_frame`.
   - Reference-to-video: prompt, one or more images with role
     `reference_image`.
5. Node submits `content_generation.tasks.create` to ModelArk.
6. Node polls `content_generation.tasks.get` until success/failure unless
   non-blocking mode is selected.
7. On success, node downloads or wraps the generated video for ComfyUI and
   returns response metadata.

## Error Handling

- Missing API key should fail before any network call with a clear message.
- `last_frame_image` without `first_frame_image` should fail locally.
- FLF2V inputs and reference inputs should be mutually exclusive for the first
  pass, matching Jimeng's current safety behavior.
- BytePlus API errors should include the model ID and a compact version of the
  payload, with image data truncated.
- Live API failures should not return silent blank outputs unless explicitly
  requested by an ignore-errors path.

## Testing

Unit tests should cover:

- API key precedence.
- model display name to model ID mapping.
- FLF2V content payload roles and validation.
- reference-image content payload roles and validation.
- duration/aspect-ratio fallback behavior.
- no secret leakage in logged/debug payloads.

Manual verification should cover:

- Importing the custom node in a ComfyUI environment.
- Running a minimal FLF2V workflow with tiny input images.
- Running a reference-image-to-video workflow with one or two reference images.
- Confirming output video and response metadata are usable downstream.

## Open Questions

- The user said "seedream2", but the requested workflows are video workflows.
  This design treats that as Seedance 2.0.
- Whether BytePlus accepts the same `return_last_frame` parameter used by the
  Jimeng/Volcano SDK path needs to be verified. If not, extract the last frame
  locally from the generated video.
- Whether `byteplussdkarkruntime` is preferable to
  `volcenginesdkarkruntime` in ComfyUI needs quick runtime validation.
