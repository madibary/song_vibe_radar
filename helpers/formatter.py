import re

# remove reasoning from the model's response if it includes a <think>...</think> block, leaving only the content
def get_content_only(description: str) -> str:
    # If the model prepends a <think>...reasoning...</think> block, strip it
    parts = re.split(r"</think\s*>", description, maxsplit=1)
    if len(parts) > 1:
        content = parts[1].strip()
    else:
        # No closing </think> found — remove a leading <think...> tag if present
        content = re.sub(r"^<think[^>]*>", "", description).strip()
    return content