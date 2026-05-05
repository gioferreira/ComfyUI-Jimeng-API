import os


BYTEPLUS_BASE_URL = "https://ark.ap-southeast.bytepluses.com/api/v3"

SEEDANCE2_MODELS = {
    "Seedance 2.0": "dreamina-seedance-2-0-260128",
    "Seedance 2.0 Fast": "dreamina-seedance-2-0-fast-260128",
}


class BytePlusConfigError(RuntimeError):
    pass


def get_api_key():
    for env_name in ("ARK_API_KEY", "BYTEPLUS_API_KEY"):
        value = os.environ.get(env_name)
        if value and value.strip():
            return value.strip()

    raise BytePlusConfigError(
        "BytePlus API key not found. Set ARK_API_KEY or BYTEPLUS_API_KEY."
    )


def resolve_seedance2_model(display_name):
    try:
        return SEEDANCE2_MODELS[display_name]
    except KeyError as exc:
        raise BytePlusConfigError(
            f"Unknown Seedance 2.0 model: {display_name}"
        ) from exc
