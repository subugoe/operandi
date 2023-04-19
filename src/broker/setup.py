# -*- coding: utf-8 -*-
from setuptools import setup

install_requires = open('requirements.txt').read().split('\n')

setup(
    name='operandi_broker',
    version='1.5.0',
    description='OPERANDI - Service Broker',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Mehmed Mustafa',
    author_email='mehmed.mustafa@gwdg.de',
    url='https://github.com/subugoe/operandi',
    license='Apache License 2.0',
    packages=['operandi_broker'],
    package_data={'': ['batch_scripts/*.sh', 'nextflow_workflows/*.nf']},
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'operandi-broker=operandi_broker:cli',
        ]
    },
)
