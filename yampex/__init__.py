#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# yampex:
# Yet Another Matplotlib Extension
#
# Copyright (C) 2017-2020 by Edwin A. Suominen,
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

from contextlib import contextmanager

from .plot import Plotter


@contextmanager
def xyc(*args, **kw):
    """
    Call L{xy} in context. Yields a L{SpecialAx} object for the
    (single) subplot in context so you can add to it. Then shows the
    plot.
    """
    plot = kw.pop('plot', None)
    dots = kw.pop('dots', False)
    pt = Plotter(1, **kw)
    with pt as sp:
        if dots:
            sp.add_line(':')
            sp.add_marker('o')
        sp.use_grid()
        if plot is None:
            sp.set_zeroLine()
            func = sp
        else: func = getattr(sp, plot)
        yield func(*args)
    pt.show()
    
def xy(*args, **kw):
    """
    A quick way to do a simple plot with a grid and zero-crossing
    line. You can provide one or more vectors to plot as args. If two
    or more, the first one will be used for the x axis.

    @keyword plot: Set to the name of a plot type, e.g., "semilogy" if
        a particular plot type is desired.

    @keyword dots: Set C{True} to show a marker at each coordinate
        pair.

    @keyword figSize: Set to a 2-sequence with figure width and height
        if not using the default, which is just shy of your entire
        monitor size. Dimensions are in inches, converted to pixels at
        100 DPI, unless both are integers and either exceeds 75. Then
        they are considered to specify the pixel dimensions directly.

    @keyword width: Specify the figure width part of I{figSize}.
        
    @keyword height: Specify the figure height part of I{figSize}.

    @see: L{xyc}, on which this function is based.
    """
    with xyc(*args, **kw) as sp:
        pass


    
    
