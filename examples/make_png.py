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


import time

import numpy as np
from yampex import Plotter

class SinCos(object):
    funcNames = ('sin', 'cos')
    filePath = "sc.png"

    def __init__(self):
        self.X = np.linspace(0, 4*np.pi, 200)
        self.pt = Plotter(1, 2, width=7, height=5, useAgg=True)
        self.pt.set_title("Sin and Cosine")
        self.pt.set_xlabel("X")
        self.pt.set_grid()
        self.pt.add_annotation(0, "First")
        self.pt.add_annotation(199, "Last")

    def __call__(self, frequency):
        with self.pt as p:
            for funcName in self.funcNames:
                Y = getattr(np, funcName)(frequency*self.X)
                p.set_ylabel("{}(X)".format(funcName))
                p(self.X, Y)
        with open(self.filePath, "wb") as fh:
            self.pt.show(fh=fh)

# Use the linux command 'qiv -Te sc.png' to watch the updating plots
# with shrinking sin/cos magnitudes.
            
if __name__ == "__main__":
    sc = SinCos()
    for frequency in np.linspace(1.0, 10.0, 20):
        sc(frequency)
        time.sleep(1.0)
