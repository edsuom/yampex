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
Demo of Annotator. This is unfortunately the closest thing to a
unit test for the yampex package.

I figured it would be hard to write a proper test suite for an
inherently graphical package. But after way too much time spent
running little demo programs over and over to debug stuff, I regret
not at least trying to unit test some lower-level classes.
"""

import numpy as np
from yampex import plot, annotate
from yampex.util import sub


class Figure(object):
    def __init__(self):
        self.p = plot.Plotter(1, verbose=True, width=500, height=500)

    def plot(self):
        with self.p as sp:
            sp.use_grid()
            #sp.add_annotation(1, "Annotation")
            sp.add_annotation(2, "Another")
            sp([-1, 0, +1], [-1, 0, +1])
        self.p.show()
        

def run():
    # Plot the curves
    Figure().plot()


if __name__ == '__main__':
    run()
