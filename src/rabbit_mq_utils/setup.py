# -*- coding: utf-8 -*-
from setuptools import setup

install_requires = open('requirements.txt').read().split('\n')

setup(
    name='rabbit_mq_utils',
    version='1.0.0',
    description='OPERANDI - RabbitMQ Utilities',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Mehmed Mustafa',
    author_email='mehmed.mustafa@gwdg.de',
    url='https://github.com/subugoe/operandi',
    license='Apache License 2.0',
    packages=['rabbit_mq_utils'],
    package_data={'': ['config.toml', '*.json', '*.yml', '*.xml']},
    install_requires=install_requires,
    keywords=['OPERANDI']
)
