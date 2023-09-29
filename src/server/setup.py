# -*- coding: utf-8 -*-
from setuptools import setup
from operandi_utils import OPERANDI_VERSION

install_requires = open('requirements.txt').read().split('\n')
install_requires.append(f'operandi_utils == {OPERANDI_VERSION}')

setup(
    name='operandi_server',
    version=OPERANDI_VERSION,
    description='OPERANDI - Server',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Mehmed Mustafa',
    author_email='mehmed.mustafa@gwdg.de',
    url='https://github.com/subugoe/operandi',
    license='Apache License 2.0',
    packages=[
        'operandi_server',
        'operandi_server.models',
        'operandi_server.routers'
    ],
    package_data={},
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'operandi-server=operandi_server:cli',
        ]
    },
)
