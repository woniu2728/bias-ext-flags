from django.apps import AppConfig


class FlagsExtensionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    label = "flags"
    name = "bias_ext_flags.backend"
    verbose_name = "Bias Flags Extension"

