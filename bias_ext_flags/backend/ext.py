from bias_ext_flags.backend.extenders import (
    admin_extenders,
    event_extenders,
    frontend_extenders,
    model_extenders,
    resource_extenders,
    service_extenders,
    settings_extenders,
)


def extend():
    return [
        *frontend_extenders(),
        *settings_extenders(),
        *admin_extenders(),
        *service_extenders(),
        *resource_extenders(),
        *model_extenders(),
        *event_extenders(),
    ]
