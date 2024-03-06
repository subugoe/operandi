# -*- coding: utf-8 -*-
from setuptools import setup

install_requires = open('requirements.txt').read().split('\n')

setup(
    name='operandi_utils',
    version='2.10.3',
    description='OPERANDI - Utils',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Mehmed Mustafa',
    author_email='mehmed.mustafa@gwdg.de',
    url='https://github.com/subugoe/operandi',
    license='Apache License 2.0',
    packages=[
        'operandi_utils',
        'operandi_utils.database',
        'operandi_utils.hpc',
        'operandi_utils.rabbitmq'
    ],
    package_data={'': ['batch_scripts/*.sh', 'nextflow_workflows/*.nf']},
    install_requires=install_requires
)
