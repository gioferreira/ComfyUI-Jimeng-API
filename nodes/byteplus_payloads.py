import copy


class BytePlusPayloadError(ValueError):
    pass


def _image_content(data_url, role):
    return {
        "type": "image_url",
        "image_url": {"url": data_url},
        "role": role,
    }


def _clean_data_urls(values):
    return [value for value in values if value]


def build_seedance2_task_kwargs(
    *,
    model,
    prompt,
    first_frame_data_url=None,
    last_frame_data_url=None,
    reference_image_data_urls=None,
    resolution="720p",
    ratio="adaptive",
    duration=5,
    generate_audio=False,
    seed=-1,
):
    prompt = (prompt or "").strip()
    reference_image_data_urls = _clean_data_urls(reference_image_data_urls or [])

    has_first_last = bool(first_frame_data_url or last_frame_data_url)
    has_references = bool(reference_image_data_urls)

    if last_frame_data_url and not first_frame_data_url:
        raise BytePlusPayloadError("A first frame is required when using a last frame.")

    if has_first_last and has_references:
        raise BytePlusPayloadError(
            "First/last frame inputs cannot be mixed with reference images."
        )

    if not prompt and not has_first_last and not has_references:
        raise BytePlusPayloadError("Seedance 2.0 requires a prompt or visual input.")

    content = []
    if prompt:
        content.append({"type": "text", "text": prompt})

    if first_frame_data_url:
        content.append(_image_content(first_frame_data_url, "first_frame"))
    if last_frame_data_url:
        content.append(_image_content(last_frame_data_url, "last_frame"))

    for data_url in reference_image_data_urls:
        content.append(_image_content(data_url, "reference_image"))

    if ratio == "adaptive" and not has_first_last and not has_references:
        ratio = "16:9"

    payload = {
        "model": model,
        "content": content,
        "resolution": resolution,
        "ratio": ratio,
        "duration": duration,
        "generate_audio": bool(generate_audio),
    }

    if seed is not None and seed != -1:
        payload["seed"] = seed

    return payload


def compact_payload_for_log(payload, max_chars=120):
    def compact(value):
        if isinstance(value, dict):
            return {key: compact(item) for key, item in value.items()}
        if isinstance(value, list):
            return [compact(item) for item in value]
        if isinstance(value, str) and value.startswith("data:") and len(value) > max_chars:
            return value[:max_chars] + f"...<truncated:{len(value) - max_chars}>"
        return value

    return compact(copy.deepcopy(payload))
