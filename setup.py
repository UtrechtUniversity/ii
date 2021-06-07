from setuptools import setup

setup(
    author="Sietse Snel",
    author_email="s.t.snel@uu.nl",
    description=('Command line utilities for iRODS'),
    install_requires=[
        'python-irodsclient~=0.9.0',
        'psutil>=5.0.0',
        'Columnar~=1.3.1',
        'humanize~=3.7.1',
        'PyYAML~=5.4.1'
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
