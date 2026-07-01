from dataclasses import dataclass
from typing import Any, Optional

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from bias_core.extensions.platform import dispatch_forum_event_after_commit
from bias_ext_flags.backend.events import PostFlagCreatedEvent, PostFlagsDeletedEvent, PostFlagsResolvedEvent
from bias_ext_flags.backend.models import PostFlag


def apply_runtime_model_visibility(*args, **kwargs):
    from bias_core.extensions.runtime import apply_runtime_model_visibility as runtime_apply_model_visibility

    return runtime_apply_model_visibility(*args, **kwargs)


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


def ensure_user_not_suspended(user, action_label: str = "") -> None:
    _service_method(get_runtime_service("users.service"), "ensure_not_suspended")(user, action_label)


def has_forum_permission(user, permission_names) -> bool:
    return bool(_service_method(get_runtime_service("users.service"), "has_forum_permission")(user, permission_names))


def get_post_action_context(*args, **kwargs):
    return _service_method(get_runtime_service("content.posts"), "get_action_context")(*args, **kwargs)


class PostActionContextNotFound(ValueError):
    pass


@dataclass(frozen=True)
class PostActionContext:
    id: int
    discussion_id: int
    user_id: int | None
    number: int | None
    hidden_at: Any = None
    discussion_title: str = ""


def report_post(post_id: int, user: Any, reason: str, message: str = "") -> PostFlag:
    ensure_user_not_suspended(user, "举报帖子")
    post = require_post_action_context(post_id, user=user, require_visible=True)

    if not user or not user.is_authenticated:
        raise PermissionDenied("请先登录")
    if post.user_id == user.id and not _can_flag_own_post():
        raise ValueError("不能举报自己的帖子")
    if post.hidden_at is not None:
        raise ValueError("该帖子已被隐藏")

    try:
        existing = PostFlag.objects.get(
            post_id=post.id,
            user=user,
            status=PostFlag.STATUS_OPEN,
        )
        existing.reason = reason
        existing.message = message
        existing.save(update_fields=["reason", "message"])
        return existing
    except PostFlag.DoesNotExist:
        flag = PostFlag.objects.create(
            post_id=post.id,
            user=user,
            reason=reason,
            message=message,
        )
        dispatch_forum_event_after_commit(
            PostFlagCreatedEvent(
                flag_id=flag.id,
                post_id=post.id,
                discussion_id=post.discussion_id,
                actor_user_id=user.id,
            )
        )
        return flag


def get_flag_list(status: Optional[str] = None, page: int = 1, limit: int = 20, *, user: Any | None = None):
    queryset = PostFlag.objects.select_related(
        "post",
        "post__discussion",
        "post__user",
        "user",
        "resolved_by",
    )

    if status:
        queryset = queryset.filter(status=status)

    if user is not None:
        queryset = apply_runtime_model_visibility(
            PostFlag,
            queryset,
            {"user": user, "ability": "view"},
        )

    total = queryset.count()
    offset = (page - 1) * limit
    return list(queryset[offset:offset + limit]), total


def resolve_flag(flag_id: int, admin_user: Any, status: str, resolution_note: str = "") -> PostFlag:
    if status not in {PostFlag.STATUS_RESOLVED, PostFlag.STATUS_IGNORED}:
        raise ValueError("无效的处理状态")

    flag = PostFlag.objects.select_related("post", "post__discussion", "user").get(id=flag_id)
    flag.status = status
    flag.resolution_note = resolution_note
    flag.resolved_by = admin_user
    flag.resolved_at = timezone.now()
    flag.save(update_fields=["status", "resolution_note", "resolved_by", "resolved_at"])
    dispatch_forum_event_after_commit(
        PostFlagsResolvedEvent(
            flag_ids=(flag.id,),
            post_id=flag.post_id,
            discussion_id=flag.post.discussion_id,
            actor_user_id=admin_user.id,
            status=status,
        )
    )
    return flag


def resolve_post_flags(post_id: int, admin_user: Any, status: str, resolution_note: str = "") -> int:
    if not admin_user.is_staff:
        raise PermissionDenied("只有管理员可以处理举报")
    if status not in {PostFlag.STATUS_RESOLVED, PostFlag.STATUS_IGNORED}:
        raise ValueError("无效的处理状态")

    open_flags = list(PostFlag.objects.select_related("post").filter(post_id=post_id, status=PostFlag.STATUS_OPEN))
    if not open_flags:
        raise ValueError("当前帖子没有待处理举报")

    resolved_at = timezone.now()
    for flag in open_flags:
        flag.status = status
        flag.resolution_note = resolution_note
        flag.resolved_by = admin_user
        flag.resolved_at = resolved_at

    PostFlag.objects.bulk_update(
        open_flags,
        ["status", "resolution_note", "resolved_by", "resolved_at"],
    )
    first_flag = open_flags[0]
    dispatch_forum_event_after_commit(
        PostFlagsResolvedEvent(
            flag_ids=tuple(flag.id for flag in open_flags),
            post_id=post_id,
            discussion_id=first_flag.post.discussion_id,
            actor_user_id=admin_user.id,
            status=status,
        )
    )
    return len(open_flags)


def delete_post_flags(post_id: int, user: Any) -> int:
    post = require_post_action_context(post_id, user=user, require_visible=True)
    if not has_forum_permission(user, "admin.flag.delete"):
        raise PermissionDenied("无权删除举报")

    with transaction.atomic():
        flag_ids = tuple(PostFlag.objects.filter(post_id=post.id).values_list("id", flat=True))
        if not flag_ids:
            return 0
        PostFlag.objects.filter(id__in=flag_ids).delete()
        dispatch_forum_event_after_commit(
            PostFlagsDeletedEvent(
                flag_ids=flag_ids,
                post_id=post.id,
                discussion_id=post.discussion_id,
                actor_user_id=user.id,
            )
        )
        return len(flag_ids)


def require_post_action_context(post_id: int, user: Any = None, *, require_visible: bool = True) -> PostActionContext:
    context = get_post_action_context(post_id, user=user, require_visible=require_visible)
    if context is None:
        raise PostActionContextNotFound("帖子不存在")
    return PostActionContext(
        id=int(context["id"]),
        discussion_id=int(context["discussion_id"]),
        user_id=context.get("user_id"),
        number=context.get("number"),
        hidden_at=context.get("hidden_at"),
        discussion_title=str(context.get("discussion_title") or ""),
    )


def _can_flag_own_post() -> bool:
    from bias_core.extensions.platform import get_extension_settings

    settings = get_extension_settings("flags")
    return bool(settings.get("can_flag_own", False))

