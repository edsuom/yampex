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

"""
Do everything with a Plotter in context.
"""

import numpy as np


class Scaler(object):
    """
    Multiples go like this: 1000, 500, 200, 100, 50, 20, 10, 5, 1, 0.5, ...
    """
    mantissas = 10, 5, 2, 1
    initialExponent = 3
    minExponent = -7
    maxCrossoverFraction = 0.4

    def __init__(self, X):
        self.X = X
        self.Xmax = X.max()
        self.ssX = 0.9 * sum(np.square(X))
        self.maxCrossoverN = self.maxCrossoverFraction * len(X)

    def tryScale(self, Y, multiplier, ignoreCrossover=False):
        Ym = multiplier*Y
        if Ym.max() > self.Xmax or sum(np.square(Ym)) > self.ssX:
            # Sum of squares under X has to be greater than that under Y
            return False
        if ignoreCrossover:
            return True
        Z = np.greater(Ym, self.X)
        if not np.any(Z):
            # No crossover, this will work
            return True
        # One crossover region is also OK, if Y is still below
        # X most of the time
        K = np.nonzero(Z)[0]
        if len(K) > self.maxCrossoverN:
            # Too much crossover time
            return False
        if len(K) < 20:
            # It's tiny, this is fine no matter what
            return True
        # Skip a small fragment on the ends of the crossover
        # region to accomodate slight noise
        K = K[8:-8]
        # No skipped indices == one continuous region
        if np.ediff1d(K).max() == 1:
            return True
        
    def __call__(self, Y):
        """
        Returns an appropriate scaling factor for 1-D numpy array I{Y}
        relative to my base array I{X}.
        """
        for ignoreCrossover in (False, True):
            k = -1
            exponent = self.initialExponent
            while True:
                k += 1
                if k == len(self.mantissas):
                    k = 0
                    exponent -= 1
                    if exponent < self.minExponent:
                        # No suitable multiplier found
                        break
                multiplier = self.mantissas[k] * 10**exponent
                if self.tryScale(Y, multiplier, ignoreCrossover):
                    return multiplier
        return 1.0
