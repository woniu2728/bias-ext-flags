from __future__ import annotations

from bias_core.extensions import (
    ResourceEndpointDefinition,
    ResourceFieldDefinition,
    ResourceRelationshipDefinition,
)

from bias_ext_flags.backend.constants import EXTENSION_ID
from bias_ext_flags.backend.handlers import (
    dispatch_post_delete_flags,
    dispatch_post_report,
    dispatch_post_resolve_flags,
)
from bias_ext_flags.backend.resource import FlagResource
from bias_ext_flags.backend.resources import (
    post_flag_preload_resolver,
    resolve_admin_open_flags,
    resolve_forum_can_view_flags,
    resolve_forum_flag_count,
    resolve_post_can_flag,
    resolve_post_can_moderate_flags,
    resolve_post_flag_identifiers,
    resolve_post_open_flag_count,
    resolve_post_open_flags,
    resolve_post_viewer_has_open_flag,
    resolve_user_new_flag_count,
)


def flag_resource_definitions():
    return (
        FlagResource(),
    )


def forum_resource_field_definitions():
    return (
        ResourceFieldDefinition(
            resource="forum",
            field="can_view_flags",
            module_id=EXTENSION_ID,
            resolver=resolve_forum_can_view_flags,
            description="当前用户是否可以查看举报队列。",
        ),
        ResourceFieldDefinition(
            resource="forum",
            field="flag_count",
            module_id=EXTENSION_ID,
            resolver=resolve_forum_flag_count,
            description="当前用户可见的待处理举报帖子数量。",
            visible=_visible_to_forum_flag_moderators,
        ),
    )


def admin_stats_resource_field_definitions():
    return (
        ResourceFieldDefinition(
            resource="admin_stats",
            field="openFlags",
            module_id=EXTENSION_ID,
            resolver=resolve_admin_open_flags,
            description="后台统计中的待处理举报数量。",
        ),
    )


def post_resource_field_definitions():
    return (
        ResourceFieldDefinition(
            resource="post",
            field="can_flag",
            module_id=EXTENSION_ID,
            resolver=resolve_post_can_flag,
            description="当前用户是否可以举报该回复。",
        ),
        ResourceFieldDefinition(
            resource="post",
            field="viewer_has_open_flag",
            module_id=EXTENSION_ID,
            resolver=resolve_post_viewer_has_open_flag,
            description="当前用户是否已对该回复提交待处理举报。",
            preload_resolver=post_flag_preload_resolver,
        ),
        ResourceFieldDefinition(
            resource="post",
            field="open_flag_count",
            module_id=EXTENSION_ID,
            resolver=resolve_post_open_flag_count,
            description="当前回复的待处理举报数量。",
            preload_resolver=post_flag_preload_resolver,
        ),
        ResourceFieldDefinition(
            resource="post",
            field="open_flags",
            module_id=EXTENSION_ID,
            resolver=resolve_post_open_flags,
            description="当前回复的待处理举报明细。",
            preload_resolver=post_flag_preload_resolver,
        ),
        ResourceFieldDefinition(
            resource="post",
            field="can_moderate_flags",
            module_id=EXTENSION_ID,
            resolver=resolve_post_can_moderate_flags,
            description="当前用户是否可在前台处理举报。",
        ),
    )


def user_detail_resource_field_definitions():
    return (
        ResourceFieldDefinition(
            resource="user_detail",
            field="new_flag_count",
            module_id=EXTENSION_ID,
            resolver=resolve_user_new_flag_count,
            description="当前用户可见的待处理举报帖子数量。",
            visible=_visible_to_self,
        ),
    )


def post_resource_relationship_definitions():
    return (
        ResourceRelationshipDefinition(
            resource="post",
            relationship="flags",
            module_id=EXTENSION_ID,
            resolver=resolve_post_flag_identifiers,
            description="当前回复可见的待处理举报关系。",
            visible=_visible_to_flag_moderators,
            resource_type="flag",
            many=True,
            plain_output="linkage",
            preload_resolver=post_flag_preload_resolver,
        ),
    )


def post_resource_endpoint_definitions():
    return (
        ResourceEndpointDefinition(
            resource="post",
            endpoint="report",
            module_id=EXTENSION_ID,
            handler=dispatch_post_report,
            methods=("POST",),
            path="posts/{object_id}/report",
            absolute_path=True,
            auth_required=True,
        ),
        ResourceEndpointDefinition(
            resource="post",
            endpoint="flags/resolve",
            module_id=EXTENSION_ID,
            handler=dispatch_post_resolve_flags,
            methods=("POST",),
            path="posts/{object_id}/flags/resolve",
            absolute_path=True,
            auth_required=True,
        ),
        ResourceEndpointDefinition(
            resource="post",
            endpoint="flags/delete",
            module_id=EXTENSION_ID,
            handler=dispatch_post_delete_flags,
            methods=("DELETE",),
            path="posts/{object_id}/flags",
            absolute_path=True,
            auth_required=True,
        ),
    )


def _visible_to_flag_moderators(post, context: dict) -> bool:
    return resolve_forum_can_view_flags(None, context)


def _visible_to_forum_flag_moderators(forum, context: dict) -> bool:
    return resolve_forum_can_view_flags(forum, context)


def _visible_to_self(user, context: dict) -> bool:
    actor = context.get("user")
    return bool(actor and actor.is_authenticated and user and actor.id == user.id)
