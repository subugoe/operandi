# -*- coding: utf-8 -*-
from setuptools import setup

install_requires = open('requirements.txt').read().split('\n')

setup(
    name='harvester',
    version='1.2.0',
    description='OPERANDI - Harvester',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Mehmed Mustafa',
    author_email='mehmed.mustafa@gwdg.de',
    url='https://github.com/subugoe/operandi',
    license='Apache License 2.0',
    packages=['harvester'],
    package_data={'': ['*.txt', '*.nf']},
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'operandi-harvester=harvester:cli',
        ]
    },
)
