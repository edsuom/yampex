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
More complicated demo of annotations. Resize the plot window and
watch the annotations get intelligently repositioned!
"""

import numpy as np
from yampex import plot, annotate
from yampex.util import sub


class Figure(object):
    verbose = False
    
    def __init__(self):
        self.p = plot.Plotter(2, verbose=self.verbose, width=1000, height=1000)
        self.p.use_timex()
        self.p.use_grid()

    def add_annotations(self, k, prefix):
        for kVector in (0, 1):
            text = sub("{}, {}", prefix, "upper" if kVector else "lower")
            self.sp.add_annotation(k, text, kVector=kVector)
        
    def plot(self):
        X = np.linspace(0, 2e-6, 100)
        with self.p as self.sp:
            for m in (1, 3):
                Y = np.tanh(m*2e6*(X-1e-6))
                self.add_annotations(0, "Start")
                self.add_annotations(50, "Midway")
                self.add_annotations(55, "Near Midway")
                self.add_annotations(99, "Finish")
                self.sp(X, Y-0.1, Y+0.1)
        self.p.show()
        

def run():
    # Plot the curves
    Figure().plot()


if __name__ == '__main__':
    run()
