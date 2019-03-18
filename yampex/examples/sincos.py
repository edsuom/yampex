#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# yampex:
# Yet Another Matplotlib Extension
#
# Copyright (C) 2017-2019 by Edwin A. Suominen,
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
A sine and cosine plot in each of two subplots, with a call to the
L{SpecialAx} object.
"""

import numpy as np
from yampex import Plotter

# Construct a Plotter object for a 700x500 pixel (100 DPI) figure with
# two subplots.
pt = Plotter(1, 2, width=7.0, height=5.0)
# The plots, one in each subplot, will be of a sine and cosine with
# 200 points from 0 to 4*pi.
funcNames = ('sin', 'cos')
X = np.linspace(0, 4*np.pi, 200)
pt.set_title("Sine and Cosine")
# Each subplot will have an x-axis label of "X" and a grid.
pt.set_xlabel("X"); pt.use_grid()
# Each plot will have an annotation labeled "Last" at its last
# point. Note that we can use negative indices referenced to the last
# element, just as with Python sequences.
pt.add_annotation(-1, "Last")

# Make a subplotting context and work with the two subplots via the
# subplot tool sp. It's actually just a reference to pt, but set up
# for subplotting, with a context for a new subplot each time it's
# called.
with pt as sp:
    # Do each plot, sin and then cos.
    for funcName in funcNames:
        # Generate the 1-D Numpy array for this plot's y-axis.
        Y = getattr(np, funcName)(X)
        # The sin plot will have a dashed line instead of the default
        # solid line
        if funcName == 'sin': sp.add_line(':')
        # Each subplot will have a y-axis label indicating its
        # mathematical function
        sp.set_ylabel("{}(X)".format(funcName))
        # Add annotations to the subplot that show locations of the
        # positive-going zero crossing, maximum, negative-going zero
        # crossing, and minimum
        k = 0 if funcName == 'sin' else 75
        for text in ("Pos ZC", "Max", "Neg ZC", "Min"):
            # The annotation is added with the integer index of the
            # point it annotates and its text.
            sp.add_annotation(k, text)
            # The next annotation will be 25 indices further along.
            k += 25
        # Add a vertical line at the second positive-going zero crossing
        sp.add_axvline(k)
        # Call the subplotting tool to plot X and Y and advance to the
        # next subplot.
        sp(X, Y)
# Show the subplots.
pt.show()
