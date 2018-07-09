from django.test import TestCase

from impersonate_auth.backends import ImpersonationBackendMixin

from .base import TEST_USER, TEST_SUPERUSER
from .base import BaseImpersonationBackendTest

SILLY_BACKEND = 'tests.backends.SillyBackend'
SILLY_IMP_BACKEND = 'tests.backends.SillyImpersonationBackend'


class TestSillyImpersonationBackend(BaseImpersonationBackendTest, TestCase):
    backends = [SILLY_IMP_BACKEND, SILLY_BACKEND]
    user_name = TEST_USER['email']
    user_pw = TEST_USER['email'][::-1]
    superuser_name = TEST_SUPERUSER['email']
    superuser_pw = TEST_SUPERUSER['email'][::-1]
    impersonation_backend = SILLY_IMP_BACKEND

    def test_impersonation_login_password_contains_sep(self):
        pass # test doesn't apply for this backend
