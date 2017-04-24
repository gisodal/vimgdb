from setuptools import setup

setup(
    name='vimgdb',
    version='1.0.0',
    zip_safe=False,
    description='Use Vim to visually step through source code with GNU Gdb.',
    keywords='Vim Gdb Tmux debugger',
    license='MIT',
    url='https://github.com/gisodal/vimgdb',
    packages=['vimgdb'],
    package_data={'vimgdb': ['config/vimrc','config/gdbinit']},
    scripts = ['bin/vimgdb'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Software Development',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: MIT License'
    ]
    )
