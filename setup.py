from setuptools import setup
from vimgdb import Version

setup(
    name='vimgdb',
    version=Version(),
    zip_safe=False,
    description='Use Vim to visually step through source code with GNU Gdb.',
    keywords='Vim Gdb Tmux debugger',
    license='MIT',
    url='https://github.com/gisodal/vimgdb',
    packages=['vimgdb'],
    package_data={'vimgdb': ['config/vimrc','config/gdbinit']},
    scripts = ['bin/vimgdb'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Topic :: Software Development :: Debuggers',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: MIT License'
    ]
    )
