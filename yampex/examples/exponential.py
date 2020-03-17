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
Plots of an exponential function M{a*exp(-b*X)} for different
values of I{a} and I{b}.

There are two subplots, a top one for a range of interest for I{X} and
a bottom one for positive values of I{X} from zero to double the
maximum I{X} in the range of interest.

This example shows how a subplot can contain both a legend and an
annotation.
"""

import numpy as np
from yampex import Plotter
from yampex.util import sub


class CurvePlotter(object):
    """
    I do the plotting.
    """
    width = 1400
    height = 1200
    xMin, xMax = 5.0, 8.0
    N = 100
    
    def __init__(self):
        """
        Constructs a Yampex Plotter object for a figure with two subplots.
        """
        self.pt = Plotter(2, width=self.width, height=self.height)
        self.pt.use_grid()
        self.pt.set_title(
            "Exponentials plotted from {:.1f} to {:.1f}", self.xMin, self.xMax)
        self.pt.set_xlabel("X")
        self.pt.set_ylabel("a*exp(-b*X)")

    def func(self, X, a, b):
        """
        The exponential function M{a*exp(-b*X)}
        """
        return a*np.exp(-b*X)

    def leastDiff(self, Ys, logspace=False):
        """
        Returns the index of the vectors of I{Ys} where there is the least
        difference between their values.

        Set I{logspace} C{True} to have the difference calculated in
        logspace, for a semilog plot.
        """
        Z = np.row_stack(Ys)
        if logspace: Z = np.log(Z)
        V = np.var(Z, axis=0)
        return np.argmin(V)
    
    def subplot(self, sp, X, aVals, bVals, semilog=False):
        """
        Given the subplotting tool I{sp} and the supplied 1-D Numpy array
        of I{X} values, plots the curves for each combination of I{a}
        in I{aVals} and I{b} in I{bVals}.

        Returns the value of I{X} where there is the least difference
        between the curves.
        """
        Ys = []
        for a, b in zip(aVals, bVals):
            Ys.append(self.func(X, a, b))
            sp.add_legend("a={:.2f}, b={:.2f}", a, b)
        k = self.leastDiff(Ys, semilog)
        sp.add_annotation(k, X[k])
        if semilog:
            sp.semilogy(X, *Ys)
        else: sp(X, *Ys)
                
    def plot(self, aVals, bVals):
        """
        Plots the curves for each combination of I{a} in I{aVals} and its
        corresponding I{b} in I{bVals}, from my I{xMin} to my I{xMax}
        and from zero to double my I{xMax}.
        """
        with self.pt as sp:
            # Top subplot: The range of interest
            X = np.linspace(self.xMin, self.xMax, self.N)
            self.subplot(sp, X, aVals, bVals)
            # Bottom subplot: Positive X surrounding the range of
            # interest
            X = np.linspace(0, 2*self.xMax, self.N)
            sp.add_axvline(self.xMin)
            sp.add_axvline(self.xMax)
            self.subplot(sp, X, aVals, bVals, semilog=True)
        self.pt.show()


def run():
    bVals = [0.2,   0.5,   1.0,   2.0,   3.0]
    aVals = [0.25,  1.3,  17.0, 2.8E3, 4.0E5]
    # Plot the curves
    CurvePlotter().plot(aVals, bVals)


if __name__ == '__main__':
    run()
