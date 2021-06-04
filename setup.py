from setuptools import setup

setup(
    author="Sietse Snel",
    author_email="s.t.snel@uu.nl",
    description=('Command line utilities for iRODS'),
    install_requires=[
        'python-irodsclient~=0.8.2',
        'psutil>=5.0.0'
    ],
    name='ii_irods',
    packages=[
        'ii_irods'],
    entry_points={
        'console_scripts': [
            'ii = ii_irods.ii_command:entry',
        ]
    },
    version='0.0.1',
)
