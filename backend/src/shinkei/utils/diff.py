"""Unified diff generation utilities."""
import difflib
from typing import Optional


def generate_unified_diff(
    original: str,
    modified: str,
    fromfile: str = "original",
    tofile: str = "modified",
    lineterm: str = "",
) -> str:
    """
    Generate a unified diff between original and modified text.

    Args:
        original: Original text content
        modified: Modified text content
        fromfile: Label for original file (default: "original")
        tofile: Label for modified file (default: "modified")
        lineterm: Line terminator (default: empty string)

    Returns:
        Unified diff string in git-style format

    Example:
        >>> original = "Line 1\\nLine 2\\nLine 3"
        >>> modified = "Line 1\\nLine 2 modified\\nLine 3"
        >>> diff = generate_unified_diff(original, modified)
        >>> print(diff)
        --- original
        +++ modified
        @@ -1,3 +1,3 @@
         Line 1
        -Line 2
        +Line 2 modified
         Line 3
    """
    # Split into lines for difflib
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)

    # Generate unified diff
    diff_lines = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile=fromfile,
        tofile=tofile,
        lineterm=lineterm,
    )

    # Join the diff lines
    return "".join(diff_lines)


def generate_field_diff(
    original: Optional[str],
    modified: Optional[str],
    field_name: str,
) -> Optional[str]:
    """
    Generate a unified diff for a specific field.

    Handles cases where original or modified might be None.

    Args:
        original: Original field value (can be None)
        modified: Modified field value (can be None)
        field_name: Name of the field being compared

    Returns:
        Unified diff string, or None if both values are None or identical
    """
    # If both are None or both are the same, no diff
    if original == modified:
        return None

    # Handle None cases
    original_text = original if original is not None else ""
    modified_text = modified if modified is not None else ""

    # Generate diff
    return generate_unified_diff(
        original_text,
        modified_text,
        fromfile=f"original_{field_name}",
        tofile=f"modified_{field_name}",
    )


def generate_beat_modification_diff(
    original_content: str,
    modified_content: str,
    original_summary: Optional[str] = None,
    modified_summary: Optional[str] = None,
    original_time_label: Optional[str] = None,
    modified_time_label: Optional[str] = None,
) -> str:
    """
    Generate a comprehensive unified diff for a beat modification.

    Includes diffs for content and any modified metadata fields.

    Args:
        original_content: Original beat content
        modified_content: Modified beat content
        original_summary: Original summary (optional)
        modified_summary: Modified summary (optional)
        original_time_label: Original time label (optional)
        modified_time_label: Modified time label (optional)

    Returns:
        Combined unified diff string showing all changes
    """
    diffs = []

    # Content diff (always present)
    content_diff = generate_unified_diff(
        original_content,
        modified_content,
        fromfile="original_content",
        tofile="modified_content",
    )
    if content_diff:
        diffs.append("=== Content ===\n" + content_diff)

    # Summary diff (if changed)
    summary_diff = generate_field_diff(original_summary, modified_summary, "summary")
    if summary_diff:
        diffs.append("=== Summary ===\n" + summary_diff)

    # Time label diff (if changed)
    time_label_diff = generate_field_diff(
        original_time_label, modified_time_label, "time_label"
    )
    if time_label_diff:
        diffs.append("=== Time Label ===\n" + time_label_diff)

    return "\n\n".join(diffs) if diffs else ""
