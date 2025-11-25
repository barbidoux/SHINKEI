"""Utilities for smart JSON truncation and text handling."""
import json
from typing import Any, Dict, List, Optional
from shinkei.logging_config import get_logger

logger = get_logger(__name__)


# MEDIUM PRIORITY FIX 3.1: Token limit constants
MAX_TEXT_LENGTH = 10000  # ~2500 tokens, safe for most models
MAX_BACKDROP_LENGTH = 500
MAX_LAWS_LENGTH = 500
MAX_METADATA_LENGTH = 300


def truncate_text_for_extraction(
    text: str,
    max_length: int = MAX_TEXT_LENGTH
) -> str:
    """
    MEDIUM PRIORITY FIX 3.1: Truncate text to prevent token overflow.

    Args:
        text: Text to potentially truncate
        max_length: Maximum character length

    Returns:
        Truncated text with indicator if truncated
    """
    if not text or len(text) <= max_length:
        return text

    logger.warning(
        "text_truncated_for_extraction",
        original_length=len(text),
        truncated_length=max_length
    )

    # Truncate at a sentence boundary if possible
    truncated = text[:max_length]

    # Try to end at a sentence
    last_period = truncated.rfind('. ')
    if last_period > max_length * 0.8:  # Only use if it's not too short
        truncated = truncated[:last_period + 1]

    return truncated + "\n\n[Text truncated for processing...]"


def smart_truncate_json(
    data: Optional[Dict[str, Any]],
    max_length: int = 500,
    max_keys: int = 5
) -> str:
    """
    HIGH PRIORITY FIX 2.4: Truncate JSON while preserving valid structure.

    Instead of slicing a JSON string at arbitrary position (which creates
    invalid JSON), this function intelligently summarizes large JSON objects.

    Strategy:
    1. If data is None or empty, return "{}"
    2. If JSON string is within limit, return as-is
    3. If too long, keep only top-level keys with "..." as values
    4. If still too long, limit number of keys

    Args:
        data: Dictionary to truncate
        max_length: Maximum string length for output
        max_keys: Maximum number of top-level keys to keep

    Returns:
        Valid JSON string within length limit
    """
    if not data:
        return "{}"

    # Try full JSON first
    try:
        full_json = json.dumps(data, indent=2)
        if len(full_json) <= max_length:
            return full_json
    except (TypeError, ValueError) as e:
        logger.warning("json_serialization_failed", error=str(e))
        return "{}"

    # Get top-level keys
    keys = list(data.keys())[:max_keys]

    # Create summarized version with truncated values
    summarized: Dict[str, Any] = {}
    for key in keys:
        value = data[key]
        if isinstance(value, str):
            # Truncate long strings
            summarized[key] = value[:100] + "..." if len(value) > 100 else value
        elif isinstance(value, (dict, list)):
            # Replace complex structures with type indicator
            if isinstance(value, dict):
                summarized[key] = f"{{...{len(value)} items}}"
            else:
                summarized[key] = f"[...{len(value)} items]"
        else:
            # Keep primitives as-is
            summarized[key] = value

    # Add ellipsis if we truncated keys
    if len(data) > max_keys:
        summarized["..."] = f"(+{len(data) - max_keys} more)"

    try:
        result = json.dumps(summarized, indent=2)
        if len(result) <= max_length:
            return result

        # If still too long, be more aggressive
        compact_summary = {k: "..." for k in keys[:3]}
        if len(data) > 3:
            compact_summary["..."] = f"(+{len(data) - 3} more)"
        return json.dumps(compact_summary)

    except (TypeError, ValueError):
        return "{}"


def smart_truncate_list(
    items: Optional[List[Dict[str, Any]]],
    max_items: int = 10,
    key_fields: Optional[List[str]] = None
) -> str:
    """
    Truncate a list of entities while preserving key identifying information.

    Args:
        items: List of entity dictionaries
        max_items: Maximum number of items to include
        key_fields: Fields to preserve (e.g., ["name", "type"])

    Returns:
        JSON string of truncated list
    """
    if not items:
        return "[]"

    key_fields = key_fields or ["name"]
    truncated = []

    for item in items[:max_items]:
        if isinstance(item, dict):
            truncated.append({k: item.get(k, "") for k in key_fields if k in item})
        else:
            truncated.append(str(item))

    try:
        result = json.dumps(truncated, indent=2)
        return result
    except (TypeError, ValueError):
        return "[]"


def smart_truncate_metadata(
    metadata: Optional[Dict[str, Any]],
    max_length: int = 300
) -> str:
    """
    Truncate entity metadata while preserving key information.

    Args:
        metadata: Entity metadata dictionary
        max_length: Maximum string length

    Returns:
        Valid JSON string within length limit
    """
    if not metadata:
        return "{}"

    # Priority fields to keep
    priority_fields = [
        "role", "importance", "aliases", "personality_traits",
        "location_type", "significance", "atmosphere"
    ]

    # Try full metadata first
    try:
        full_json = json.dumps(metadata, indent=2)
        if len(full_json) <= max_length:
            return full_json
    except (TypeError, ValueError):
        return "{}"

    # Keep only priority fields
    filtered = {}
    for field in priority_fields:
        if field in metadata:
            value = metadata[field]
            if isinstance(value, str) and len(value) > 50:
                filtered[field] = value[:50] + "..."
            elif isinstance(value, list) and len(value) > 3:
                filtered[field] = value[:3] + ["..."]
            else:
                filtered[field] = value

    try:
        return json.dumps(filtered, indent=2)
    except (TypeError, ValueError):
        return "{}"
