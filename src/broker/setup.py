# -*- coding: utf-8 -*-
from setuptools import setup
from operandi_utils.constants import OPERANDI_VERSION

install_requires = open('requirements.txt').read().split('\n')
install_requires.append(f'operandi_utils == {OPERANDI_VERSION}')

setup(
    name='operandi_broker',
    version=OPERANDI_VERSION,
    description='OPERANDI - Service Broker',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Mehmed Mustafa',
    author_email='mehmed.mustafa@gwdg.de',
    url='https://github.com/subugoe/operandi',
    license='Apache License 2.0',
    packages=['operandi_broker'],
    package_data={},
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'operandi-broker=operandi_broker:cli',
        ]
    },
)
