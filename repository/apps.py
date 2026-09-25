from django.apps import AppConfig


class RepositoryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "repository"

    def ready(self):
        # TEMP: CARTO_API_KEY diagnostics. Runs after settings are fully loaded
        # and the app registry is populated -- the best point to compare the raw
        # env var against the resolved Django setting. Remove once resolved.
        from score.carto_debug import probe

        probe("RepositoryConfig.ready (settings fully loaded)", check_setting=True)
