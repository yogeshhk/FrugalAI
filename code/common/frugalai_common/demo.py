"""Shared pieces for the per-project Streamlit demo pages (code/<project>/app.py).

Nothing here imports Streamlit at module level, so the tests run without it. The UI-free parts live in
`machine.py` (machine, Wi-Fi, models served) and `netguard.py` (the offline guard); they are re-exported here so
the pages need one import.

- install_guard(): from then on, this Python process refuses every connection and name lookup that is not to this
  machine, and counts both kinds. Switching the Wi-Fi off is the visible proof; the counter is the second one.
- sidebar(st, needs): the panel every page shows: machine, Wi-Fi, LM Studio models, connection counts.
- page(st, title): page config, the shared style and the localhost check.
"""

import os
from typing import Dict

from .machine import lm_models, machine, machine_lines, wifi_state  # noqa: F401  (re-exported for the pages)
from .netguard import Blocked, Guard, install, is_local, uninstall  # noqa: F401

os.environ.setdefault("HF_HUB_OFFLINE", "1")                    # no Hugging Face lookups from any demo page
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

GUARD = Guard()   # the process-wide guard every demo page turns on


def install_guard(guard: Guard = GUARD) -> Guard:
    """Refuse every connect(), sendto() and name lookup to another machine for the rest of the process. Idempotent."""
    return install(guard)


def uninstall_guard(guard: Guard = GUARD) -> None:
    """Turn the guard off again (tests only; a demo page keeps it on)."""
    uninstall(guard)


def bind_problem(address) -> str:
    """Empty string when the Streamlit server is bound to this machine only, else the message to show."""
    return "" if str(address or "") in ("localhost", "127.0.0.1", "::1") else (
        "This page must be served on localhost only: streamlit run app.py --server.address localhost")


def sidebar(st, needs: Dict[str, str] = None, guard: Guard = GUARD, note: str = "") -> None:
    """The panel every demo page shows. `needs` maps a role (chat, embedding) to the model id the page uses."""
    sb = st.sidebar
    sb.markdown("### This machine")
    for line in machine_lines(machine()):
        sb.markdown("- " + line)
    wifi = wifi_state()
    sb.markdown("### Offline")
    sb.markdown("- Wi-Fi: **%s**" % wifi)
    sb.markdown("- Internet connections from this page: **%d blocked**, %d to this machine"
                % (len(guard.blocked), guard.local))
    models = lm_models()
    sb.markdown("### Models")
    if models is None:
        sb.markdown("- LM Studio: not running")
    else:
        for role, mid in (needs or {}).items():
            sb.markdown("- %s: `%s` %s" % (role, mid, "loaded" if mid in models else "**not loaded**"))
    if note:
        sb.caption(note)


PAGE_CSS = """<style>
#MainMenu, header, footer { visibility: hidden; }
.block-container { padding-top: 2rem; max-width: 1350px; }
html, body, [class*="css"] { font-size: 19px; }
.big { font-size: 1.5em; font-weight: 600; margin: 0.6rem 0 0.8rem 0; }
.h { font-size: 1.0em; font-weight: 600; color: #555; margin: 0.8rem 0 0.3rem 0; }
.a { font-size: 1.15em; line-height: 1.5; }
.note { color: #666; font-size: 0.8em; margin-top: 1.6rem; }
.ok { color: #1b7f3b; font-weight: 600; } .warn { color: #b26a00; font-weight: 600; } .bad { color: #b00020; font-weight: 600; }
</style>"""


def page(st, title: str, subtitle: str = "") -> None:
    """Page config, the shared style and the localhost check. Call first in every app.py."""
    st.set_page_config(page_title=title, layout="wide")
    bad = bind_problem(st.get_option("server.address"))
    if bad:
        st.error(bad)
        st.stop()
    st.markdown(PAGE_CSS, unsafe_allow_html=True)
    st.markdown("## " + title)
    if subtitle:
        st.caption(subtitle)
