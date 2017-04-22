from setuptools import setup

setup(
    name='vimgdb',
    zip_safe=False,
    license='MIT',
    packages=['vimgdb'],
    package_data={'vimgdb': ['config/vimrc','config/gdbinit']}
    )
