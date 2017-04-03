#!/usr/bin/env python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-


import io
import sys
from setuptools import setup
#from distutils.core import setup
from setuptools.command.test import test as TestCommand


def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)


class PyTestCommand(TestCommand):
    """ Command to run unit py.test unit tests
    """
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['test/tests.py']
        self.test_suite = True

    def run(self):
        import pytest
        rcode = pytest.main(self.test_args)
        sys.exit(rcode)


setup(
    name='vimrunner',
    version='1.0.3',
    description='Interface for controlling a Vim editor using Python code.',
    long_description=read('README.rst'),
    author='Andrei Chiver',
    author_email='andreichiver@gmail.com',
    license='MIT',
    url='https://github.com/andri-ch/vimrunner-python',
    #provides=['vimrunner'],
    #py_modules=['vimrunner'],
    #package_dir=['vimrunner'],
    packages=['vimrunner'],
    package_data={'vimrunner': ['default_vimrc']},
    #data_files=[('', ['default_vimrc'])],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Software Development',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'License :: OSI Approved :: MIT License',
    ],
    keywords='test Vim editor server plugin',
    tests_require=[
        'pytest',
    ],
    cmdclass={
        'test': PyTestCommand,
        # so you can do at the command line:
        # python setup.py test
    },
)
