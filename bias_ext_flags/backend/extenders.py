from __future__ import annotations

from bias_core.extensions import (
    AdminSurfaceExtender,
    ApiResourceExtender,
    ApiRoutesExtender,
    LifecycleExtender,
    ModelExtender,
    ModelVisibilityExtender,
    PostLifecycleExtender,
    RuntimeServiceContractExtender,
    SettingsExtender,
    ServiceProviderExtender,
)

from bias_ext_flags.backend.admin_api import router as flags_admin_router
from bias_ext_flags.backend.admin_surface import admin_page_definitions, permission_definitions
from bias_ext_flags.backend.frontend import frontend_extender
from bias_ext_flags.backend.lifecycle import prepare_post_delete_flags
from bias_ext_flags.backend.model_contracts import flag_model_visibility_definitions, owned_models
from bias_ext_flags.backend.realtime_contracts import realtime_extender
from bias_ext_flags.backend.resource_contracts import (
    admin_stats_resource_field_definitions,
    flag_resource_definitions,
    forum_resource_field_definitions,
    post_resource_endpoint_definitions,
    post_resource_field_definitions,
    post_resource_relationship_definitions,
    user_detail_resource_field_definitions,
)
from bias_ext_flags.backend.runtime import flag_service_provider
from bias_ext_flags.backend.settings import setting_definitions


def frontend_extenders():
    return (frontend_extender(),)


def settings_extenders():
    return (
        SettingsExtender(
            fields=setting_definitions(),
            expose_to_forum=("guidelines_url",),
        ),
    )


def admin_extenders():
    return (
        AdminSurfaceExtender(
            permissions=permission_definitions(),
            admin_pages=admin_page_definitions(),
            permissions_pages=("/admin/extensions/flags/permissions",),
            operations_pages=("/admin/extensions/flags/operations",),
        ),
        ApiRoutesExtender(
            mounts=(("/admin", flags_admin_router),),
            tags=("Admin",),
        ),
    )


def resource_extenders():
    return (
        *(ApiResourceExtender(definition) for definition in flag_resource_definitions()),
        ApiResourceExtender("forum").fields(forum_resource_field_definitions),
        ApiResourceExtender("admin_stats").fields(admin_stats_resource_field_definitions),
        ApiResourceExtender("post")
        .fields(post_resource_field_definitions)
        .relationships(post_resource_relationship_definitions)
        .endpoints(post_resource_endpoint_definitions)
        .add_default_include(("index", "show"), ("flags",)),
        ApiResourceExtender("user_detail").fields(user_detail_resource_field_definitions),
    )


def model_extenders():
    extender = ModelExtender()
    for model, description in owned_models():
        extender = extender.owns(model, description=description)
    return (
        extender,
        ModelVisibilityExtender(
            definitions=flag_model_visibility_definitions(),
        ),
    )


def event_extenders():
    return (
        realtime_extender(),
        PostLifecycleExtender().handler(
            "flags",
            prepare_delete=prepare_post_delete_flags,
            description="帖子删除前清理关联举报并派发举报删除事件。",
        ),
    )


def service_extenders():
    return (
        ServiceProviderExtender(
            key="flags.service",
            provider=flag_service_provider,
        ),
        RuntimeServiceContractExtender().service(
            "flags.service",
            required_values=(
                "model",
                "status_ignored",
                "status_open",
                "status_resolved",
            ),
            required_methods=(
                "delete_post_flags",
                "get_flag_list",
                "report_post",
                "resolve_flag",
                "resolve_post_flags",
            ),
        ),
        LifecycleExtender(),
    )
