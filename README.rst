Django Impersonate Auth
=======================
|build| |coverage| |contributors| |license|

Django Impersonate Auth is a simple drop in authentication backend that allows
superusers to impersonate regular users in the system.

Impersonation is handled by signing in using the target user's username and the
superuser's username and password, separated by a specific character, as the
password.

Getting Started
---------------

To install this library, you can simply run ::

    pip install -e git+https://github.com/JordanReiter/django-impersonate-auth.git#egg=django-impersonate-auth

Then add ::

       'impersonate_auth.backends.ImpersonationBackend',
    

to the ``AUTHENTICATION_BACKENDS`` setting. If you don't currently have a value
for ``AUTHENTICATION_BACKENDS``, you can add this to your settings file, which
includes the default backend plus
the impersonation backend (both are required to function correctly)::

    AUTHENTICATION_BACKENDS = [
        'django.contrib.auth.backends.ModelBackend',
        'impersonate_auth.backends.ImpersonationBackend',
    ]

Usage
-----

Using the default separator, a colon, here is an example of how to impersonate
another (non superuser) user:

- | Normal User:  
  | Username: ``testuser``  
  | Password: ``12345``  

- | Super User:
  | Username: ``superuser``
  | Password: ``987654321``

- | Super User impersonating Normal User:
  | Username: ``testuser``
  | Password: ``superuser:987654321``

Settings
--------

The default separator is a colon, but this can be changed using the
``IMPERSONATE_AUTH_SEPARATOR`` setting. The following code changes it to an
exclamation mark::

    IMPERSONATE_AUTH_SEPARATOR = '!'

With this setting, in the example above, Super User would impersonate Normal
User using the password ``superuser!987654321``.

Using Custom Authentication Backends
------------------------------------

The package provides a mixin, ``ImpersonationBackendMixin``, which should
provide all the necessary code to implement impersonation for any authentication
backend which uses a combination of username and password. The backend uses the
``USERNAME_FIELD`` property of the user model, so if you use a custom User model
which uses a different field (for example, E-mail address) then it will still
work correctly.

Adding impersonation to your custom backend just means creating a new class that
extends both your existing and ``ImpersonationBackendMixin``. For example,
imagine a very insecure authentication backend called ``SillyBackend`` where the
password is simply the username spelled backwards::

    from django.contrib.auth.backends import ModelBackend
    from django.contrib.auth import get_user_model

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


In order to implement the impersonation functionality, you would add the
following code to your ``backends.py`` file::

    from impersonate_auth.backends import ImpersonationBackendMixin

    class SillyImpersonationBackend(ImpersonationBackendMixin, SillyBackend):
        def __init__(self, *args, **kwargs):
            super(SillyImpersonationBackend, self).__init__(*args, **kwargs)

No other coding needed! Just make sure to add
``path.to.backends.SillyImpersonationBackend`` to your
``AUTHENTICATION_BACKENDS`` setting.


Signals
-------

In order to log or track impersonation, each time you log in using an
impersonation login, a ``user_impersonated`` signal is sent. If it fails, a
``user_impersonation_failed`` signal is triggered. Note that these signals are
only triggered if the login would have been a success with the correct login.
That is, they are not triggered if the user you are trying to impersonate does
not exist or would not be available for some other reason (e.g. they are
inactive).

Credits
-------
Thanks to Daniele Faraglia <https://github.com/joke2k> and the django-environ
project <https://github.com/joke2k/django-environ>. Both my .travis.yml file
and this readme were partially modeled on the respective files from that
project.

.. |coverage| image:: https://img.shields.io/coveralls/JordanReiter/django-impersonate-auth/master.svg?style=flat-square
    :target: https://coveralls.io/r/JordanReiter/django-impersonate-auth?branch=master
    :alt: Test coverage

.. |build| image:: https://travis-ci.org/JordanReiter/django-impersonate-auth.svg?branch=master
    :target: https://travis-ci.org/JordanReiter/django-impersonate-auth

.. |windows_build|  image:: https://img.shields.io/appveyor/ci/JordanReiter/django-impersonate-auth.svg?style=flat-square&logo=windows
    :target: https://ci.appveyor.com/project/JordanReiter/django-impersonate-auth
    :alt: Build status of the master branch on Windows


.. |contributors| image:: https://img.shields.io/github/contributors/JordanReiter/django-impersonate-auth.svg?style=flat-square
    :target: https://github.com/JordanReiter/django-impersonate-auth/graphs/contributors

.. |license| image:: https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square
    :target: https://raw.githubusercontent.com/JordanReiter/django-impersonate-auth/master/LICENSE
    :alt: Package license

.. _`the repository`: https://github.com/JordanReiter/django-impersonate-auth