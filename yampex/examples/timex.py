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
A grid of subplots that each show a pair of amplitude-modulated
waveforms at different time scales.

Illustrates the use of L{options.OptsBase.use_timex} and calls to a
subplot-context instance of L{plot.Plotter} with multiple y-axis
arguments. Also shows a couple of intelligently-positioned
annotations.
"""

import numpy as np
from yampex import Plotter

EQs = ("sin(10*t)*cos(10000*t)", "cos(10*t)*cos(10000*t)")

N = 6
t = np.linspace(0, 2E-6, 1000)
# This time, we specify the plot dimensions in pixels with a tuple
pt = Plotter(N, figSize=(1600, 1200))
pt.set_title("With {:d} time scales: {}, {}", N, *EQs)
pt.use_timex()
pt.use_grid()
for eq in EQs:
    pt.add_legend(eq)
with pt as sp:
    for mult in range(N):
        X = t*10**mult
        Y1 = np.sin(10*X)*np.sin(10000*X)
        Y2 = np.cos(10*X)*np.cos(10000*X)
        sp.set_title("0 - {:.5g} seconds", X[-1])
        if mult < 5 and np.any(Y2 < 0):
            sp.add_annotation(0.0, "Zero Crossing", kVector=1, y=True)
        sp(X, Y1, Y2)
pt.show()
