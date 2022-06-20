# -*- coding: utf-8 -*-
from setuptools import setup

install_requires = open('requirements.txt').read().split('\n')

setup(
  name='priority_queue',
  version='0.0.1',
  description='OPERANDI - Message Queue - RabbitMQ Server',
  long_description=open('README.md').read(),
  long_description_content_type='text/markdown',
  author='Mehmed Mustafa',
  author_email='mehmed.mustafa@gwdg.de',
  url='https://github.com/MehmedGIT/OPERANDI_TestRepo',
  license='Apache License 2.0',
  packages=['priority_queue'],
  install_requires=install_requires,
  package_data={'': ['*.json', '*.yml', '*.xml']},
  keywords=['OPERANDI']
)
