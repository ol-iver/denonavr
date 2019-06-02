#!/usr/bin/env python3
# encoding: utf-8
"""Automation Library for Denon AVR receivers."""
from setuptools import find_packages, setup

setup(name='denonavr',
      version='0.7.9',
      description='Automation Library for Denon AVR receivers',
      long_description='Automation Library for Denon AVR receivers',
      url='https://github.com/scarface-4711/denonavr',
      author='Oliver Goetz',
      author_email='scarface@mywoh.de',
      license='MIT',
      packages=find_packages(),
      install_requires=['requests'],
      tests_require=['tox'],
      platforms=['any'],
      zip_safe=False,
      classifiers=[
          "Development Status :: 4 - Beta",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: BSD License",
          "Operating System :: OS Independent",
          "Topic :: Software Development :: Libraries",
          "Topic :: Home Automation",
          "Programming Language :: Python :: 3.4",
          "Programming Language :: Python :: 3.5",
          "Programming Language :: Python :: 3.6",
          ])
