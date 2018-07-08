from django.test import TestCase, override_settings

from .base import BaseImpersonationBackendTest, AUTH_BACKEND


class TestImpersonationBackend(BaseImpersonationBackendTest, TestCase):
    backends = [AUTH_BACKEND, 'django.contrib.auth.backends.ModelBackend']
    pass
