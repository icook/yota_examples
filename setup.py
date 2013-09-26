#!/usr/bin/env python
import sys
from setuptools import setup, find_packages

try:
    script = sys.argv.pop(1)
except IndexError:
    script = ""

if script == "flask":
    setup(name='flask_example',
        version='0.1',
        description='Use case examples for the form library Yota',
        packages=['flask_example'],
        install_requires=['yota',
            'jinja2',
            'flask',
        ])
elif script == "circuits":
    setup(name='circuits_example',
        version='0.1',
        description='Use case examples for the form library Yota',
        packages=['circuits_example'],
        install_requires=['yota',
            'jinja2',
            'circuits'
        ])
elif script == "django":
    setup(name='django_example',
        version='0.1',
        description='Use case examples for the form library Yota',
        packages=['django_example'],
        install_requires=['yota',
            'jinja2',
            'django'
        ])
else:
    print("This is not a normal setup.py, just must specify which example you"
          " would like to install. Specify either flask, circuits, or django")
