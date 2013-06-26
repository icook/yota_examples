import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

requires = ['yota',
        'jinja2',
        'flask',
        'django>=1.5'
]

setup(name='yota_examples',
      version='0.1',
      description='Use case examples for the form library Yota',
      long_description="",
      author='',
      url='',
      packages=find_packages('src'),
      include_package_data=True,
      install_requires=requires,
      package_dir = {'': 'src'},
      )
