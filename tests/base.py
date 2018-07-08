import uuid

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import AbstractUser
from django.test import TestCase, override_settings, Client, modify_settings


from impersonate_auth import signals


TEST_USER_NAME = str(uuid.uuid4())
TEST_USER_PW = 'NormalPassword'
TEST_USER = {
    'email': '{}@example.org'.format(TEST_USER_NAME),
    'first_name': 'FirstNormal',
    'last_name': 'LastNormal',
    'password': TEST_USER_PW
}

TEST_SUPERUSER_NAME = 'super{}'.format(str(uuid.uuid4())[:8])
TEST_SUPERUSER_PW = 'SuperPassword'
TEST_SUPERUSER = {
    'email': '{}@example.org'.format(TEST_SUPERUSER_NAME),
    'first_name': 'FirstNormal',
    'last_name': 'LastNormal',
    'password': TEST_SUPERUSER_PW
}


AUTH_BACKEND = 'impersonate_auth.backends.ImpersonationBackend'
NORMAL_SEP = ':'
ALT_SEP = '^'


class BaseImpersonationBackendTest:
    backends = ['django.contrib.auth.backends.ModelBackend']

    user_name = TEST_USER_NAME
    user_pw = TEST_USER_PW
    superuser_name = TEST_SUPERUSER_NAME
    superuser_pw = TEST_SUPERUSER_PW
    impersonation_backend = AUTH_BACKEND

    def setUp(self, *args, **kwargs):
        self.client = Client()
        self.user = self.create_user(self.user_name, **TEST_USER)
        self.superuser = self.create_superuser(
            self.superuser_name, TEST_SUPERUSER.get('email'), self.superuser_pw,
            **{kk: vv for kk, vv in TEST_SUPERUSER.items() if kk not in ('email', 'password')}
        )
        self.patched_settings = modify_settings(
            AUTHENTICATION_BACKENDS={'append': self.backends},
            INSTALLED_APPS={'append': 'tests'},
        )
        self.patched_settings.enable()
        signals.user_impersonated.connect(self.add_user_impersonated)
        signals.user_impersonation_failed.connect(self.add_user_impersonation_failed)
        self.received_signals = []

    def add_received_signal(self, signal_name, sender, *args, **kwargs):
        kwargs.pop('signal', None)
        self.received_signals.append((signal_name, sender, args, kwargs))

    def add_user_impersonated(self, *args, **kwargs):
        self.add_received_signal('user_impersonated', *args, **kwargs)

    def add_user_impersonation_failed(self, *args, **kwargs):
        self.add_received_signal('user_impersonation_failed', *args, **kwargs)

    def tearDown(self):
        self.patched_settings.disable()

    def login(self, username=None, password=None):
        UserModel = get_user_model()
        creds = {
            UserModel.USERNAME_FIELD: username,
            'password': password
        }
        return self.client.login(**creds)

    def create_user(self, *args, **kwargs):
        UserModel = get_user_model()
        return UserModel.objects.create_user(*args, **kwargs)

    def create_superuser(self, *args, **kwargs):
        UserModel = get_user_model()
        return UserModel.objects.create_superuser(*args, **kwargs)

    def test_impersonation_login_normal_sep(self):
        impersonate_pw = '{}{}{}'.format(
            self.superuser_name, NORMAL_SEP, self.superuser_pw
        )
        success = self.login(username=self.user_name, password=impersonate_pw)
        self.assertTrue(success)
        logged_in_user = authenticate(username=self.user_name, password=impersonate_pw)
        self.assertEqual(logged_in_user, self.user)
        self.assertEqual(logged_in_user.backend, self.impersonation_backend)
        self.assertFalse(logged_in_user.is_superuser)

    def test_impersonation_wrong_password(self):
        impersonate_pw = '{}{}{}'.format(
            self.superuser_name, NORMAL_SEP, 'WRONG-PASSWORD'
        )
        success = self.login(username=self.user_name, password=impersonate_pw)
        self.assertFalse(success)
        logged_in_user = authenticate(username=self.user_name, password=impersonate_pw)
        self.assertIsNone(logged_in_user)

    @override_settings(IMPERSONATE_AUTH_SEPARATOR=ALT_SEP)
    def test_impersonation_login_alt_sep(self):
        impersonate_pw = '{}{}{}'.format(
            self.superuser_name, ALT_SEP, self.superuser_pw
        )
        success = self.login(username=self.user_name, password=impersonate_pw)
        self.assertTrue(success)
        logged_in_user = authenticate(username=self.user_name, password=impersonate_pw)
        self.assertEqual(logged_in_user, self.user)
        self.assertEqual(logged_in_user.backend, self.impersonation_backend)
        self.assertFalse(logged_in_user.is_superuser)

    def test_password_is_none(self):
        success = self.login(username=self.superuser_name, password=None)
        self.assertFalse(success)
        logged_in_user = authenticate(username=self.superuser_name, password=None)
        self.assertIsNone(logged_in_user)

    def test_cant_impersonate_yourself(self):
        impersonate_pw = '{}{}{}'.format(
            self.superuser_name, NORMAL_SEP, self.superuser_pw
        )
        success = self.login(username=self.superuser_name, password=impersonate_pw)
        self.assertFalse(success)
        logged_in_user = authenticate(username=self.superuser_name, password=impersonate_pw)
        self.assertIsNone(logged_in_user)

    def test_cant_impersonate_nonexistent_user(self):
        impersonate_pw = '{}{}{}'.format(
            self.superuser_name, NORMAL_SEP, self.superuser_pw
        )
        non_existent_username = 'nonexistent-user'
        success = self.login(username=non_existent_username, password=impersonate_pw)
        self.assertFalse(success)
        logged_in_user = authenticate(username=non_existent_username, password=impersonate_pw)
        self.assertIsNone(logged_in_user)

    def test_cant_impersonate_superusers(self):
        other_superuser = self.create_superuser(
            str(uuid.uuid4()),
            'other.superuser@example.org',
            '12345678'
        )
        impersonate_pw = '{}{}{}'.format(
            self.superuser_name, NORMAL_SEP, self.superuser_pw
        )
        username = getattr(other_superuser, other_superuser.USERNAME_FIELD)
        success = self.login(username=username, password=impersonate_pw)
        self.assertFalse(success)
        logged_in_user = authenticate(username=username, password=impersonate_pw)
        self.assertIsNone(logged_in_user)

    def test_cant_impersonate_inactive_users(self):
        inactive_user = self.create_user(
            str(uuid.uuid4()),
            email='inactive.user@example.org',
            is_active=False
        )
        impersonate_pw = '{}{}{}'.format(
            self.superuser_name, NORMAL_SEP, self.superuser_pw
        )
        inactive_username = getattr(inactive_user, inactive_user.USERNAME_FIELD)
        success = self.login(username=inactive_username, password=impersonate_pw)
        self.assertFalse(success)
        logged_in_user = authenticate(username=inactive_username, password=impersonate_pw)
        self.assertIsNone(logged_in_user)

    def test_cant_impersonate_if_inactive(self):
        self.superuser.is_active = False
        self.superuser.save()
        impersonate_pw = '{}{}{}'.format(
            self.superuser_name, NORMAL_SEP, self.superuser_pw
        )
        success = self.login(username=self.user_name, password=impersonate_pw)
        self.assertFalse(success)
        logged_in_user = authenticate(username=self.user_name, password=impersonate_pw)
        self.assertIsNone(logged_in_user)
        self.superuser.is_active = True
        self.superuser.save()

    def test_normal_users_cant_impersonate(self):
        other_user = self.create_user(
            str(uuid.uuid4()),
            email='other.normal.user@example.org'
        )
        impersonate_pw = '{}{}{}'.format(
            self.user_name, NORMAL_SEP, self.user_pw
        )
        other_username = getattr(other_user, other_user.USERNAME_FIELD)
        success = self.login(username=other_username, password=impersonate_pw)
        self.assertFalse(success)
        logged_in_user = authenticate(username=other_username, password=impersonate_pw)
        self.assertIsNone(logged_in_user)

    def test_staff_cant_impersonate(self):
        staff_pw = 'StaffPassword'
        staff_user = self.create_user(
            str(uuid.uuid4()),
            email='staff.user@example.org',
            password=staff_pw,
            is_staff=True
        )
        self.assertTrue(staff_user.is_staff)
        other_user = self.create_user(
            str(uuid.uuid4()),
            'other.nonstaff.user@example.org'
        )
        staff_username = getattr(staff_user, staff_user.USERNAME_FIELD)
        other_username = getattr(other_user, other_user.USERNAME_FIELD)
        impersonate_pw = '{}{}{}'.format(
            staff_username, NORMAL_SEP, staff_pw
        )
        success = self.login(username=other_username, password=impersonate_pw)
        self.assertFalse(success)
        logged_in_user = authenticate(username=other_username, password=impersonate_pw)
        self.assertIsNone(logged_in_user)

    def test_success_sends_signal(self):
        UserModel = get_user_model()
        impersonate_pw = '{}{}{}'.format(
            self.superuser_name, NORMAL_SEP, self.superuser_pw
        )
        signal_count = len(self.received_signals)
        success = self.login(username=self.user_name, password=impersonate_pw)
        self.assertTrue(success)
        self.assertEqual(
            signal_count + 1,
            len(self.received_signals),
            msg="I expected to add one to {}, for a total of {}. Created signals: {}".format(signal_count, signal_count + 1, self.received_signals[signal_count:])
        )
        signal_name, sender, _, signal_kwargs = self.received_signals[-1]
        self.assertEqual(signal_name, 'user_impersonated')
        self.assertEqual(sender, UserModel)
        self.assertIn('user', signal_kwargs)
        self.assertEqual(
            signal_kwargs['user'],
            UserModel.objects.get_by_natural_key(self.user_name)
        )
        self.assertEqual(
            signal_kwargs['impersonator'],
            UserModel.objects.get_by_natural_key(self.superuser_name)
        )

    def test_failed_sends_signal(self):
        UserModel = get_user_model()
        impersonate_pw = '{}{}{}'.format(
            self.superuser_name, NORMAL_SEP, 'WRONG-PASSWORD'
        )
        signal_count = len(self.received_signals)
        success = self.login(username=self.user_name, password=impersonate_pw)
        self.assertFalse(success)
        self.assertEqual(
            signal_count + 1,
            len(self.received_signals),
            msg="I expected to add one to {}, for a total of {}. Created signals: {}".format(signal_count, signal_count + 1, self.received_signals[signal_count:])
        )
        signal_name, sender, _, signal_kwargs = self.received_signals[-1]
        self.assertEqual(signal_name, 'user_impersonation_failed')
        self.assertEqual(sender, UserModel)
        self.assertIn('user', signal_kwargs)
        self.assertEqual(
            signal_kwargs['user'],
            UserModel.objects.get_by_natural_key(self.user_name)
        )

    def test_no_user_no_signal(self):
        impersonate_pw = '{}{}{}'.format(
            self.superuser_name, NORMAL_SEP, self.superuser_pw
        )
        signal_count = len(self.received_signals)
        self.login(username='userthatdoesnotexist', password=impersonate_pw)
        self.assertEqual(
            signal_count,
            len(self.received_signals)
        )
