#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# yampex:
# Yet Another Matplotlib Extension
#
# Copyright (C) 2017-2018 by Edwin A. Suominen,
# http://edsuom.com/yampex
#
# See edsuom.com for API documentation as well as information about
# Ed's background and other projects, software and otherwise.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the
# License. You may obtain a copy of the License at
# 
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS
# IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language
# governing permissions and limitations under the License.

"""
B{Y}et B{A}nother B{M}atB{p}lotlib B{Ex}tension, with simplified
subplotting.

Everything you'll need is in the L{Plotter}.
"""

from .plot import Plotter

def xy(X, Y, **kw):
    """
    A quick way to do a simple scatter plot with a grid and
    zero-crossing line.
    """
    pt = Plotter(1, **kw)
    with pt as sp:
        if len(X) < 30: sp.add_marker('o')
        sp.use_grid(); sp.set_zeroLine()
        sp(X, Y)
    pt.show()
