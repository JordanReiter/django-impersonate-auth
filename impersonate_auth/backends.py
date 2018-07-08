from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

from django.conf import settings

from . import signals


class ImpersonationBackendMixin(object):
    def user_can_impersonate(self, user, impersonated):
        if user == impersonated:
            return False  # you can't impersonate yourself
        if not impersonated.is_active or not user.is_active:
            return False  # both users have to be active
        if impersonated.is_superuser:
            return False  # you can't impersonate other superusers
        if not user.is_superuser:
            return False
        return True

    def authenticate(self, request=None, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        SEPARATOR = getattr(settings, 'IMPERSONATE_AUTH_SEPARATOR', ':')
        impersonate_kwargs = {}
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        try:
            impersonate_user, impersonate_pass = password.split(SEPARATOR)
            if UserModel.USERNAME_FIELD != 'username':
                impersonate_kwargs[UserModel.USERNAME_FIELD] = impersonate_user
        except (ValueError, TypeError, AttributeError) as err:
            return None
        # using same code as traditional ModelBackend for retrieving impersonated user
        try:
            impersonated = UserModel._default_manager.get_by_natural_key(username)
        except UserModel.DoesNotExist:
            return None
        impersonator = super(ImpersonationBackendMixin, self).authenticate(request=request, username=impersonate_user, password=impersonate_pass, **impersonate_kwargs)
        if impersonator and self.user_can_impersonate(impersonator, impersonated):
            signals.user_impersonated.send(UserModel, request=request, user=impersonated, impersonator=impersonator)
            return impersonated
        signals.user_impersonation_failed.send(UserModel, request=request, user=impersonated)


class ImpersonationBackend(ImpersonationBackendMixin, ModelBackend):
    def __init__(self, *args, **kwargs):
        super(ImpersonationBackend, self).__init__(*args, **kwargs)
