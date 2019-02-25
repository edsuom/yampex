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


funcNames = ('sin', 'cos')
X = np.linspace(0, 4*np.pi, 200)
pt = Plotter(1, width=10, height=7)
pt.set_title("Sin and Cosine")
pt.set_xlabel("X"); pt.set_grid()
pt.add_annotation(199, "Last")
pt.add_line('-', ':')

with pt as p:
    ax = None
    for kVector, funcName in enumerate(funcNames):
        Y = getattr(np, funcName)(X)
        k = 0 if funcName == 'sin' else 75
        with p.prevOpts():
            for text in ("Pos ZC", "Max", "Neg ZC", "Min"):
                text = funcName + ":" + text
                p.add_annotation(k, text, kVector=kVector)
                k += 25
        if ax is None:
            ax = p(X, Y)
        else: ax.plot(X, Y)
pt.show()
