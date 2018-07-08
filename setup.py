import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-impersonate-auth',
    version='0.1.1',
    packages=find_packages(),
    include_package_data=True,
    license='MIT License',  # example license
    description='A simple impersonation backend for Django apps',
    long_description=README,
    url='https://github.com/JordanReiter/django-impersonate-auth',
    author='Jordan Reiter',
    author_email='jordanreiter@gmail.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',  # example license
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
    ],
)
