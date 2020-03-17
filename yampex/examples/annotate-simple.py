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
Demo of a very simple use case for L{annotate.Annotator}, with
annotation trial positioning boxes shown. (Those are for debugging
only, but it's instructive to see them once to understand how
positioning works.)
"""

import numpy as np
from yampex import plot, annotate
from yampex.util import sub


class Figure(object):
    verbose = True
    
    def __init__(self):
        annotate.Annotator.verbose = True
        self.p = plot.Plotter(1, width=500, height=500)

    def plot(self):
        with self.p as sp:
            sp.use_grid()
            sp.add_annotation(0, "Lower")
            sp.add_annotation(1, "Midway Point")
            sp.add_annotation(2, "Upper")
            sp([-1, 0, +1], [-1, 0, +1])
        self.p.show()
        

def run():
    # Plot the curves
    Figure().plot()


if __name__ == '__main__':
    run()
