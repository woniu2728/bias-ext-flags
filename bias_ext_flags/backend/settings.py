from __future__ import annotations

from bias_core.extensions import setting_field


def setting_definitions():
    return (
        setting_field({
            "key": "guidelines_url",
            "label": "社区规则 URL",
            "type": "text",
            "default": "",
            "placeholder": "https://example.com/community-guidelines",
            "help_text": "前台举报原因说明中使用的社区规则链接。",
            "order": 10,
        }),
        setting_field({
            "key": "can_flag_own",
            "label": "允许举报自己的帖子",
            "type": "boolean",
            "default": False,
            "help_text": "关闭时，帖子作者不能举报自己的帖子。",
            "order": 20,
        }),
    )
