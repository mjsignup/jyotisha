"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
import os

from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
long_description = ''
try:
  import pypandoc

  long_description = pypandoc.convert_file(source_file='README.md', to='rst', format='markdown_github')
except (IOError, ImportError):
  long_description = ''


with open('requirements.txt', 'r') as f:
  install_reqs = [
    s for s in [
      line.split('#', 1)[0].strip(' \t\n') for line in f
    ] if s != ''
  ]

setup(
  name='jyotisha',

  # Versions should comply with PEP440.  For a discussion on single-sourcing
  # the version across setup.py and the project code, see
  # https://packaging.python.org/en/latest/single_source_version.html
  version='0.1.8',

  description='Tools for computations involved in the jyotiSha vedAnga',
  long_description=long_description,

  # The project's main homepage.
  url='https://github.com/jyotisham/jyotisha',

  # Author details
  author='Sanskrit programmers',
  author_email='sanskrit-programmers@googlegroups.com',

  # Choose your license
  license='MIT',

  # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
  classifiers=[
    # How mature is this project? Common values are
    #   3 - Alpha
    #   4 - Beta
    #   5 - Production/Stable
    'Development Status :: 4 - Beta',

    # Indicate who your project is intended for
    'Intended Audience :: Education',
    'Intended Audience :: Science/Research',
    'Intended Audience :: Developers',

    # Pick your license as you wish (should match "license" above)
    'License :: OSI Approved :: MIT License',

    # Specify the Python versions you support here. In particular, ensure
    # that you indicate whether you support Python 2, Python 3 or both.
    'Programming Language :: Python :: 3',
  ],

  # What does your project relate to?
  keywords='indic vedic sanskrit astronomy astrology jyotisa jyotish jyotis, panchanga, panchaanga tithi',

  # You can just specify the packages manually here if your project is
  # simple. Or you can use find_packages().
  packages=find_packages(exclude=['contrib', 'docs', 'tests']),

  # List run-time dependencies here.  These will be installed by pip when
  # your project is installed. For an analysis of "install_requires" vs pip's
  # requirements files see:
  # https://packaging.python.org/en/latest/requirements.html
  install_requires=install_reqs,

  # List additional groups of dependencies here (e.g. development
  # dependencies). You can install these using the following syntax,
  # for example:
  # $ pip install -e .[dev,test]
  extras_require={
      'test': ['pytest'],
  },


  include_package_data = True,

  # Although 'package_data' is the preferred approach, in some case you may
  # need to place data files outside of your packages. See:
  # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
  # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
  # data_files=[('my_data', ['data/data_file'])],

  # To provide executable scripts, use entry points in preference to the
  # "scripts" keyword. Entry points provide cross-platform support and allow
  # pip to create the appropriate form of executable for the target platform.
  # entry_points={
  #     'console_scripts': [
  #         'sample=sample:main',
  #     ],
  # },
)
