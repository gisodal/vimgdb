# setup.py
from setuptools import setup

setup(
    name='vimgdb',
    license='MIT',
    packages=['vimgdb'],
    package_data={'vimgdb': ['config/vimrc','config/gdbinit']}
    )
