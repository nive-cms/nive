import os
import sys

from setuptools import setup
from setuptools import find_packages

here = os.path.abspath(os.path.dirname(__file__))

try:
    README = open(os.path.join(here, 'readme.md')).read()
    CHANGES = open(os.path.join(here, 'changes.txt')).read()
except:
    README = ''
    CHANGES = ''

requires = [
    'pyramid', 
    'iso8601', 
    'translationstring',
    'mako',
    'html2text'
]

setupkw = dict(
      name='nive',
      version='0.9.9',
      description='Nive cms - out of the box content management system for mobile and desktop websites based on the webframework pyramid',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7"
      ],
      author='Arndt Droullier, Nive GmbH',
      author_email='info@nive.co',
      url='http://cms.nive.co',
      keywords='cms website publisher pyramid',
      license='GPL 3',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="nive",
      entry_points = """\
        [pyramid.scaffold]
        defaultSqlite=nive.scaffolds:DefaultSqliteTemplate
        defaultMysql=nive.scaffolds:DefaultMysqlTemplate
      """
)

# uses babel and lingua
try:
    import babel
    babel = babel # PyFlakes
    # if babel is installed, advertise message extractors (if we pass
    # this to setup() unconditionally, and babel isn't installed,
    # distutils warns pointlessly)
    setupkw['message_extractors'] = { ".": [
        ("**.py", "lingua_python", None ),
        ("**.pt", "lingua_xml", None ),
        ]}
except ImportError:
    pass

setup(**setupkw)
