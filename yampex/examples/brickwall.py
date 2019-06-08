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
Plots of a exponential function that approaches infinity as a
brick-wall x-axis threshold is approached.
"""

import numpy as np
from yampex import xy


def func(x, xMax, transition=0.05):
    return np.exp((x/xMax-transition)/transition)

def run():
    xMax = 10.0
    X = np.linspace(0, 10.0, 200)[:-1]
    Y = func(X, xMax)
    xy(X, Y)


if __name__ == '__main__':
    run()
