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
Sine plots of increasing frequencies and amplitudes in the same
subplot, with a legend showing which plot is which.

Illustrates the use of L{options.OptsBase.add_legend}.
"""

import numpy as np
from yampex import Plotter

def vectors(N):
    """
    Returns a list with X and C{k*sin(k*X)} for I{k} from 1 to I{N},
    where X is a 1-D Numpy vector having 200 points from 0 to M{4*pi}.
    """
    X = np.linspace(0, 4*np.pi, 200)
    return [X] + [k*np.sin(k*X) for k in range(1, N+1)]


# The number of waveforms
N = 3
# Construct a Plotter object for a 800x500 pixel (specified directly
# in pixels) figure with a single subplot.
pt = Plotter(1, width=800, height=500)
# As with many methods of opts.OptsBase, you can specify the title
# with a string formatting prototype and its argument(s).
pt.set_title("Sine Waves with {:d} frequency & amplitude multipliers", N)
# The x label will say "X" and the subplot will have a grid.
pt.set_xlabel("X"); pt.use_grid()

# Make a subplotting context and work with the single subplot via the
# subplot tool sp. It's actually just a reference to pt, but set up
# for subplotting.
with pt as sp:
    # Add legends for the plots. Again, a string formatting prototype
    # and its argument are used for convenience.
    for mult in range(1, N+1):
        sp.add_legend("x{:d}", mult)
    # Plot all the vectors in a single call to the subplot tool.
    sp(*vectors(N))
# Show the single subplot.
pt.show()
