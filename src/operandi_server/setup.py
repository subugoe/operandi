# -*- coding: utf-8 -*-
from setuptools import setup

install_requires = open('requirements.txt').read().split('\n')

setup(
    name='operandi_server',
    version='1.4.1',
    description='OPERANDI - Server',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Mehmed Mustafa',
    author_email='mehmed.mustafa@gwdg.de',
    url='https://github.com/subugoe/operandi',
    license='Apache License 2.0',
    packages=['operandi_server'],
    package_data={'': ['config.toml']},
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'operandi-server=operandi_server:cli',
        ]
    },
)
