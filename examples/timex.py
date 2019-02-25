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

import numpy as np
from yampex import Plotter

EQs = ("sin(10*t)*cos(10000*t)", "cos(10*t)*cos(10000*t)")

N = 6
t = np.linspace(0, 2E-6, 1000)
pt = Plotter(N, width=6, height=5)
pt.set_title("With {:d} time scales: {}, {}", N, *EQs)
pt.set_timex()
pt.set_grid()
for eq in EQs:
    pt.add_legend(eq)
with pt as sp:
    for mult in range(N):
        X = t*10**mult
        Y1 = np.sin(10*X)*np.sin(10000*X)
        Y2 = np.cos(10*X)*np.cos(10000*X)
        sp.set_title("0 - {:.5g} seconds", X[-1])
        sp(X, Y1, Y2)
pt.show()
