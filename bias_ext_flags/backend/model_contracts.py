from __future__ import annotations

from bias_core.extensions import ExtensionModelVisibilityDefinition

from bias_ext_flags.backend.models import PostFlag
from bias_ext_flags.backend.resources import scope_flag_visibility


def owned_models():
    return (
        (
            PostFlag,
            "帖子举报记录由 flags 扩展拥有。",
        ),
    )


def flag_model_visibility_definitions():
    return (
        ExtensionModelVisibilityDefinition(
            model=PostFlag,
            ability="view",
            scope=scope_flag_visibility,
            description="限制举报记录只对可查看举报队列且能查看对应帖子的用户可见。",
        ),
    )
