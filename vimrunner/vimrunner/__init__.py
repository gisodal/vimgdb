#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:et

# create the interface of vimrunner package that contains vimrunner module
from . import vimrunner
# make Server available at the package level
from .vimrunner import Server
# now, outside of the package, one can access Server with:
# >>> from vimrunner import Server
