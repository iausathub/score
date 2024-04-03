"""
Test Django settings for score project.
"""

from socket import gethostbyname, gethostname

from .base import *  # noqa: F403

ALLOWED_HOSTS = [get_secret("score-allowed-hosts")["score-prod-alb"]]  # noqa: F405
ALLOWED_HOSTS.append(gethostbyname(gethostname()))
