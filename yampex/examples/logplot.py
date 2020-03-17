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
A log plot, with several plots in one subplot, all done in one
call to the subplotting tool in context.
"""

import numpy as np
from yampex import Plotter

# Construct a Plotter object for a 1000x800 pixel (100 DPI) figure
# with a single subplot.
pt = Plotter(1, width=10.0, height=8.0)
# The plots will be of different bases raised to powers.
X = np.linspace(0, 10, 100)
pt.set_title("Different Bases Raised to Power 0-10")
# The x label will say "Power" and the subplot will have a grid.
pt.set_xlabel("Power"); pt.use_grid()

# Make a subplotting context and work with the single subplot via the
# subplot tool sp. It's actually just a reference to pt, but set up
# for subplotting.
with pt as sp:
    # Compute the vectors all at once
    Y2 = np.power(2, X)
    Y3 = np.power(3, X)
    Y10 = np.power(10, X)
    # Just call the subplotting tool with the X-axis vector and all
    # the Ys at once.
    sp.semilogy(X, Y2, Y3, Y10, legend=["Base 2", "Base 3", "Base 10"])
# Show the single subplot.
pt.show()
