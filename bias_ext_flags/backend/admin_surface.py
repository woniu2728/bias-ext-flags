from __future__ import annotations

from bias_core.extensions import AdminPageDefinition, PermissionDefinition

from bias_ext_flags.backend.constants import EXTENSION_ID


def permission_definitions():
    return (
        PermissionDefinition(
            code="admin.flag.view",
            label="查看举报队列",
            section="moderation",
            section_label="审核与举报",
            module_id=EXTENSION_ID,
            icon="fas fa-flag",
            description="允许在后台查看帖子举报记录。",
        ),
        PermissionDefinition(
            code="admin.flag.resolve",
            label="处理帖子举报",
            section="moderation",
            section_label="审核与举报",
            module_id=EXTENSION_ID,
            icon="fas fa-gavel",
            description="允许在后台把帖子举报标记为已处理或已忽略。",
            required_permissions=("admin.flag.view",),
        ),
        PermissionDefinition(
            code="admin.flag.delete",
            label="删除帖子举报",
            section="moderation",
            section_label="审核与举报",
            module_id=EXTENSION_ID,
            icon="fas fa-trash-alt",
            description="允许删除指定的帖子举报记录。",
            required_permissions=("admin.flag.view",),
        ),
    )


def admin_page_definitions():
    return (
        AdminPageDefinition(
            path="/admin/flags",
            label="举报管理",
            icon="fas fa-flag",
            module_id=EXTENSION_ID,
            nav_section="feature",
            description="查看并处理帖子举报。",
        ),
    )
