from __future__ import annotations

from django.db.models import Prefetch

from bias_ext_flags.backend.models import PostFlag


def get_runtime_service(service_key: str, default=None):
    from bias_core.extensions.runtime import get_runtime_service as runtime_get_service

    return runtime_get_service(service_key, default)


def _service_method(service, name: str):
    if isinstance(service, dict):
        method = service.get(name)
    else:
        method = getattr(service, name, None)
    if not callable(method):
        raise RuntimeError(f"Flags 扩展运行时服务缺少方法: {name}")
    return method


def get_visible_post_ids(*args, **kwargs):
    return _service_method(get_runtime_service("content.posts"), "get_visible_ids")(*args, **kwargs)


def has_forum_permission(user, permission_names) -> bool:
    return bool(_service_method(get_runtime_service("users.service"), "has_forum_permission")(user, permission_names))


def post_flag_preload_resolver(context: dict):
    user = context.get("user")
    prefetches = []
    if user and user.is_authenticated:
        prefetches.append(
            Prefetch(
                "flags",
                queryset=PostFlag.objects.filter(
                    user=user,
                    status=PostFlag.STATUS_OPEN,
                ).select_related("post", "post__discussion", "post__user", "user", "resolved_by"),
                to_attr="viewer_open_flags_cache",
            )
        )
    if resolve_forum_can_view_flags(None, context):
        prefetches.append(
            Prefetch(
                "flags",
                queryset=PostFlag.objects.filter(status=PostFlag.STATUS_OPEN).select_related(
                    "post",
                    "post__discussion",
                    "post__user",
                    "user",
                    "resolved_by",
                ),
                to_attr="open_flags_cache",
            )
        )
    return (), tuple(prefetches)


def resolve_forum_can_view_flags(forum, context: dict) -> bool:
    user = context.get("user")
    return bool(
        user
        and user.is_authenticated
        and has_forum_permission(user, "admin.flag.view")
    )


def resolve_forum_flag_count(forum, context: dict) -> int:
    user = context.get("user")
    queryset = scope_flag_visibility(PostFlag.objects.filter(status=PostFlag.STATUS_OPEN), {"user": user})
    return queryset.values("post_id").distinct().count()


def resolve_admin_open_flags(stats, context: dict) -> int:
    return PostFlag.objects.filter(status=PostFlag.STATUS_OPEN).count()


def resolve_post_viewer_has_open_flag(post, context: dict) -> bool:
    cached = getattr(post, "viewer_open_flags_cache", None)
    if cached is not None:
        return bool(cached)
    user = context.get("user")
    if not user or not user.is_authenticated:
        return False
    return PostFlag.objects.filter(
        post_id=post.id,
        user=user,
        status=PostFlag.STATUS_OPEN,
    ).exists()


def resolve_post_can_flag(post, context: dict) -> bool:
    user = context.get("user")
    if not user or not user.is_authenticated:
        return False
    if getattr(post, "hidden_at", None) is not None:
        return False
    if post.user_id != user.id:
        return True

    from bias_core.extensions.platform import get_extension_settings

    settings = get_extension_settings("flags")
    return bool(settings.get("can_flag_own", False))


def resolve_post_open_flag_count(post, context: dict) -> int:
    cached = getattr(post, "open_flags_cache", None)
    if cached is not None:
        return len(cached)
    if not resolve_forum_can_view_flags(None, context):
        setattr(post, "open_flags_cache", [])
        return 0
    return PostFlag.objects.filter(post_id=post.id, status=PostFlag.STATUS_OPEN).count()


def resolve_post_flag_objects(post, context: dict):
    cached = getattr(post, "open_flags_cache", None)
    if cached is not None:
        return cached
    if not resolve_forum_can_view_flags(None, context):
        setattr(post, "open_flags_cache", [])
        return []
    return PostFlag.objects.filter(
        post_id=post.id,
        status=PostFlag.STATUS_OPEN,
    ).select_related("post", "post__discussion", "post__user", "user", "resolved_by")


def resolve_post_open_flags(post, context: dict) -> list[dict]:
    open_flags = resolve_post_flag_objects(post, context)
    return [
        {
            "id": flag.id,
            "reason": flag.reason,
            "message": flag.message,
            "created_at": flag.created_at,
            "user": {
                "id": flag.user.id,
                "username": flag.user.username,
                "display_name": flag.user.display_name,
            } if flag.user else None,
        }
        for flag in open_flags
    ]


def resolve_post_flags(post, context: dict) -> list[dict]:
    from bias_ext_flags.backend.handlers import serialize_flag

    return [
        serialize_flag(flag)
        for flag in resolve_post_flag_objects(post, context)
    ]


def resolve_post_flag_identifiers(post, context: dict) -> list[dict]:
    return [
        {
            "type": "flag",
            "id": str(flag.id),
        }
        for flag in resolve_post_flag_objects(post, context)
    ]


def resolve_post_can_moderate_flags(post, context: dict) -> bool:
    user = context.get("user")
    return bool(user and has_forum_permission(user, "admin.flag.view"))


def resolve_user_new_flag_count(user, context: dict) -> int:
    actor = context.get("user")
    if (
        not actor
        or not actor.is_authenticated
        or actor.id != user.id
        or not has_forum_permission(actor, "admin.flag.view")
    ):
        return 0
    queryset = scope_flag_visibility(PostFlag.objects.filter(status=PostFlag.STATUS_OPEN), {"user": actor})
    return queryset.values("post_id").distinct().count()


def scope_flag_visibility(queryset, context: dict):
    user = context.get("user")
    if (
        not user
        or not user.is_authenticated
        or not has_forum_permission(user, "admin.flag.view")
    ):
        return queryset.none()
    visible_post_ids = get_visible_post_ids(
        user=user,
        context={"skip_view_forum_gate": True},
    )
    return queryset.filter(post_id__in=visible_post_ids)

