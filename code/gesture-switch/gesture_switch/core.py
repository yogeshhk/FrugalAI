"""Plain code that sits after the gesture model: map a gesture label to an action, and ignore flicker."""

ACTIONS = {
    "thumb_up": "yes",
    "thumb_down": "no",
    "open_palm": "help",
}


def action_for(label: str) -> str | None:
    """Action name for a gesture label, or None if the label is not one we act on. Replace with the real table."""
    return ACTIONS.get(label)


def stable_label(recent: list[str], needed: int = 5) -> str | None:
    """The label only if the last `needed` frames all agree, so one noisy frame never triggers an action."""
    if len(recent) < needed:
        return None
    tail = recent[-needed:]
    return tail[0] if all(x == tail[0] for x in tail) else None
