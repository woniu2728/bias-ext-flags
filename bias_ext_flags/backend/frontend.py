from __future__ import annotations

from bias_core.extensions import FrontendExtender


def frontend_extender():
    return FrontendExtender(
        admin_entry="extensions/flags/frontend/admin/index.js",
        forum_entry="extensions/flags/frontend/forum/index.js",
    )
