# -*- coding: utf-8 -*-
from setuptools import setup

install_requires = open('requirements.txt').read().split('\n')

setup(
  name='service_broker',
  version='0.0.1',
  description='OPERANDI - Service Broker',
  long_description=open('README.md').read(),
  long_description_content_type='text/markdown',
  author='Mehmed Mustafa',
  author_email='mehmed.mustafa@gwdg.de',
  url='https://github.com/MehmedGIT/OPERANDI_TestRepo',
  license='Apache License 2.0',
  packages=['service_broker', 
            'service_broker.cli'
           ],
  install_requires=install_requires,
  entry_points={
    'console_scripts': [
        'operandi-broker=service_broker.cli:cli',
    ]
  },
)
