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
A variation of L{sincos}, with two plots in one subplot and a call
to the L{SpecialAx} object.
"""

import numpy as np
from yampex import Plotter

# Construct a Plotter object for a 1000x700 pixel (100 DPI) figure
# with a single subplot.
pt = Plotter(1, width=10.0, height=7.0)
# The plots will be of a sine (solid line) and cosine (dashed line)
# with 200 points from 0 to 4*pi.
funcNames = ('sin', 'cos')
X = np.linspace(0, 4*np.pi, 200)
pt.set_title("Sine and Cosine")
pt.add_line('-', ':')
# The x label will say "X" and the subplot will have a grid.
pt.set_xlabel("X"); pt.use_grid()

# Make a subplotting context and work with the single subplot via the
# subplot tool sp. It's actually just a reference to pt, but set up
# for subplotting.
with pt as sp:
    # Placeholder for the SpecialAx object.
    ax = None
    # Do each plot, sin and then cos.
    for kVector, funcName in enumerate(funcNames):
        # Generate the 1-D Numpy array for this plot's y-axis.
        Y = getattr(np, funcName)(X)
        # Generate annotations for this plot.
        k = 0 if funcName == 'sin' else 75
        with sp.prevOpts():
            # Add annotations to the subplot for this plot
            for text in ("Pos ZC", "Max", "Neg ZC", "Min"):
                # Add the annotation at index k, specifying that it is
                # for kVector. Annotation names have to be unique, so
                # the function name is used as a prefix. As with many
                # methods of opts.OptsBase, you can specify the text
                # with a formatting prototype and its arguments.
                sp.add_annotation(k, "{}:{}", funcName, text, kVector=kVector)
                # The next annotation will be 25 indices further along.
                k += 25
        if ax is None:
            # First plot: We just have a placeholder, so call the
            # subplotting tool and replace the placeholder with the
            # SpecialAx that we receive as a result.
            ax = sp(X, Y)
        else:
            # Second plot: Call the SpecialAx just like we called the
            # subplotting tool. We don't call the subplotting tool
            # again because that would advance us to the next subplot,
            # and this is going in the same one.
            ax.plot(X, Y)
# Show the single subplot.
pt.show()
