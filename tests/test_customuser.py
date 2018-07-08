import uuid


from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import AbstractUser
from django.test import TestCase, override_settings, Client, modify_settings

from .base import TEST_USER_NAME, TEST_USER_PW, TEST_USER
from .base import TEST_SUPERUSER_NAME, TEST_SUPERUSER_PW, TEST_SUPERUSER
from .base import BaseImpersonationBackendTest
from .base import AUTH_BACKEND


@override_settings(
    AUTH_USER_MODEL='tests.EmailUser',
)
class TestEmailImpersonationBackend(BaseImpersonationBackendTest, TestCase):
    backends = [AUTH_BACKEND]
    user_name = TEST_USER['email']
#    user_pw = TEST_USER_PW
    superuser_name = TEST_SUPERUSER['email']
#    superuser_pw = TEST_SUPERUSER_PW
    impersonation_backend = AUTH_BACKEND

    def setUp(self):
        super(TestEmailImpersonationBackend, self).setUp()

    def tearDown(self):
        super(TestEmailImpersonationBackend, self).tearDown()

    def create_user(self, username, email=None, password=None, *args, **kwargs):
        UserModel = get_user_model()
        return UserModel.objects.create_user(email, password=password, *args, **kwargs)

    def create_superuser(self, username, email, password, *args, **kwargs):
        UserModel = get_user_model()
        return UserModel.objects.create_superuser(email, password, *args, **kwargs)
