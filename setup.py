# Copyright 2017 RadicallyOpenSecurity B.V.

import os

from setuptools import setup, find_packages


version_file = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                            'VERSION'))
with open(version_file) as v:
    VERSION = v.read().strip()


SETUP = {
    'name': "pentext",
    'version': VERSION,
    'author': "RadicallyOpenSecurity",
    'url': "https://github.com/radicallyopensecurity/pentext-chatops",
    'install_requires': [
        'lxml',
        'titlecase',
        'pypandoc',
        'python-gitlab',
    ],
    'packages': find_packages(),
    'scripts': [
        'pentext/docbuilder.py',
        'pentext/gitlab-to-pentext.py',
        'pentext/pentext_id.py',
        'pentext/validate_report.py',
    ],
    'license': "GPLv3",
    'long_description': open('README.md').read(),
    'description': 'PenText system',
}


# try:
#     from sphinx_pypi_upload import UploadDoc
#     SETUP['cmdclass'] = {'upload_sphinx': UploadDoc}
# except ImportError:
#     pass

if __name__ == '__main__':
    setup(**SETUP)