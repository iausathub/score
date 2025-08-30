from django.conf import settings


def score_settings(request):
    """
    Make SCORE-specific settings available in templates.
    """
    try:
        return {
            "settings": {
                "SCORE_ACKNOWLEDGMENT_TEXT": getattr(
                    settings, "SCORE_ACKNOWLEDGMENT_TEXT", ""
                ),
            },
            "recaptcha_public_key": getattr(settings, "RECAPTCHA_PUBLIC_KEY", ""),
        }
    except Exception:
        # Fallback for test environments or when settings aren't fully loaded
        return {
            "settings": {
                "SCORE_ACKNOWLEDGMENT_TEXT": "",
            },
            "recaptcha_public_key": "",
        }
