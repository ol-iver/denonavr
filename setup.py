#!/usr/bin/env python3
# encoding: utf-8
"""Automation Library for Denon AVR receivers."""
from setuptools import find_packages, setup

setup(name='denonavr',
      version='0.10.7',
      description='Automation Library for Denon AVR receivers',
      long_description='Automation Library for Denon AVR receivers',
      url='https://github.com/scarface-4711/denonavr',
      author='Oliver Goetz',
      author_email='scarface@mywoh.de',
      license='MIT',
      packages=find_packages(),
      install_requires=[
          'asyncstdlib>=3.9.1',
          'attrs>=20.3.0',
          'defusedxml>=0.7.1',
          'httpx>=0.16.1',
          'netifaces>=0.10.9'],
      tests_require=['tox'],
      platforms=['any'],
      zip_safe=False,
      python_requires=">=3.6",
      classifiers=[
          "Development Status :: 4 - Beta",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: MIT License",
          "Operating System :: OS Independent",
          "Topic :: Software Development :: Libraries",
          "Topic :: Home Automation",
          "Programming Language :: Python :: 3.6",
          "Programming Language :: Python :: 3.7",
          "Programming Language :: Python :: 3.8",
          "Programming Language :: Python :: 3.9"
          ])
