# -*- coding: utf-8 -*-
from setuptools import setup
from operandi_utils.constants import OPERANDI_VERSION

install_requires = open('requirements.txt').read().split('\n')
install_requires.append(f'operandi_utils == {OPERANDI_VERSION}')

setup(
    name='operandi_harvester',
    version=OPERANDI_VERSION,
    description='OPERANDI - Harvester',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Mehmed Mustafa',
    author_email='mehmed.mustafa@gwdg.de',
    url='https://github.com/subugoe/operandi',
    license='Apache License 2.0',
    packages=['operandi_harvester'],
    package_data={'': ['assets/*.ocrd.zip', 'assets/*.txt', 'assets/*.nf']},
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'operandi-harvester=operandi_harvester:cli',
        ]
    },
)
