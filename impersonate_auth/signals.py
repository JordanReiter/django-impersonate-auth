from django.dispatch import Signal

user_impersonated = Signal(providing_args=['request', 'user', 'impersonator'])
user_impersonation_failed = Signal(providing_args=['request', 'user'])
