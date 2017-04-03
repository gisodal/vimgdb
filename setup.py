#!/usr/bin/env python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-

from setuptools import setup

setup(
    name='vimgdb',
    version='0.1.0',
    description='Interface combining tmux, vim and gdb.',
    author='Giso H. Dal ',
    author_email='gdal@cs.ru.nl',
    packages=['vimgdb'],
    package_data={'vimgdb': ['default_vimrc']},
    keywords='Vim gdb tmux editor',
)

