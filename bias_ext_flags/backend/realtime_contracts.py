from __future__ import annotations

from bias_core.extensions import RealtimeExtender

from bias_ext_flags.backend.events import (
    PostFlagCreatedEvent,
    PostFlagsDeletedEvent,
    PostFlagsResolvedEvent,
)


def realtime_extender():
    return (
        RealtimeExtender()
        .broadcast_discussion_event(
            PostFlagCreatedEvent,
            "post.flagged",
            include_discussion=True,
            include_post=True,
            post_id="post_id",
            description="帖子被举报后向讨论实时流广播举报状态变更。",
        )
        .broadcast_discussion_event(
            PostFlagsResolvedEvent,
            "post.flags_resolved",
            include_discussion=True,
            include_post=True,
            post_id="post_id",
            description="帖子举报被处理后向讨论实时流广播举报状态变更。",
        )
        .broadcast_discussion_event(
            PostFlagsDeletedEvent,
            "post.flags_deleted",
            include_discussion=True,
            include_post=True,
            post_id="post_id",
            description="帖子举报被删除后向讨论实时流广播举报状态变更。",
        )
    )
