import json
from typing import Any


def label_attributes_dict(attributes: Any) -> dict[str, Any]:
    if attributes is None:
        return {}

    if isinstance(attributes, str):
        try:
            attributes = json.loads(attributes)
        except ValueError:
            return {}

    if isinstance(attributes, dict):
        return attributes

    return {}
