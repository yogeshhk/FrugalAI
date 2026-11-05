"""Text clean-up and tool-call parsing for Dhir's native format.

Dhir writes a tool call as `<tool_call>{"name": ..., "arguments": {...}}</tool_call>` and ends a turn with
`<|end_of_turn|>`. The tags are special tokens, so the server decodes with special tokens kept and cleans the text
here. Pure functions, no model needed, so they are tested offline.
"""

import json
import re
import uuid
from typing import List, Tuple

# Control tokens that must never reach a client.
_CONTROL = ("<|end_of_turn|>", "<|nothink|>", "<bos>", "<pad>", "<|assistant|>", "<|user|>", "<|system|>")
_CALL_RE = re.compile(r"<tool_call>(.*?)</tool_call>", re.DOTALL)


def strip_control(text: str) -> str:
    """Remove control tokens. Tool-call tags are kept, so a caller can parse them afterwards."""
    for token in _CONTROL:
        text = text.replace(token, "")
    return text


def split_tool_calls(text: str) -> Tuple[str, List[dict]]:
    """Return (plain text, OpenAI-style tool_calls). A call that is not valid JSON stays in the text.

    Arguments are returned as a JSON string, the way the OpenAI API does.
    """
    calls = []

    def take(match):
        raw = match.group(1).strip()
        try:
            data = json.loads(raw)
            name = data["name"]
        except (ValueError, KeyError, TypeError):
            return match.group(0)
        args = data.get("arguments", {})
        if not isinstance(args, str):
            args = json.dumps(args, ensure_ascii=False)
        calls.append(
            {
                "id": "call_" + uuid.uuid4().hex[:12],
                "type": "function",
                "function": {"name": name, "arguments": args},
            }
        )
        return ""

    plain = _CALL_RE.sub(take, text)
    return plain.strip(), calls
