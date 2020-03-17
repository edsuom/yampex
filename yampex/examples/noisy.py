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
arguments.

Also illustrates how simply a row can be made twice as high as the
others.
"""

import numpy as np
from yampex import Plotter

N_sp = 4; N_pts = 200
X = np.linspace(0, 4*np.pi, N_pts)
pt = Plotter(1, 4, width=10, height=10, h2=0)
pt.set_title("Sin(X) with increasingly noisy versions")
pt.set_zeroLine()
with pt as sp:
    Y = None
    for mult in np.logspace(-1.5, +0.5, N_sp):
        if Y is None:
            sp.add_textBox(
                "SW", "This subplot is twice as high as the others.")
        Y = np.sin(X)
        Y_noisy = Y + mult*np.random.randn(N_pts)
        k = np.argmax(np.abs(Y-Y_noisy))
        sp.add_textBox("NE", "Worst: {:+.3g} vs. {:+.3g}", Y_noisy[k], Y[k])
        ax = sp(X, Y)
        ax.plot(X, Y_noisy, 'r.')
pt.show()
