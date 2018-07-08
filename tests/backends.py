from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

from impersonate_auth.backends import ImpersonationBackendMixin


class SillyBackend(ModelBackend):
    '''
    A silly backend where the password for a user is their email address backwards.
    '''

    def authenticate(self, request=None, username=None, password=None):
        UserModel = get_user_model()
        try:
            silly_user = UserModel.objects.get_by_natural_key(username)
        except UserModel.DoesNotExist:
            silly_user = None
        if silly_user and password and password[::-1] == username:
            return silly_user


class SillyImpersonationBackend(ImpersonationBackendMixin, SillyBackend):
    def __init__(self, *args, **kwargs):
        super(SillyImpersonationBackend, self).__init__(*args, **kwargs)
