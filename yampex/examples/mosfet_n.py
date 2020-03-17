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
Plots of a MOSFET's "n" value, given Vgs and its "gamma" parameter.
"""

import numpy as np
from yampex import Plotter
from yampex.util import sub


class CurvePlotter(object):
    """
    I do the plotting.
    """
    width = 1400
    height = 1400
    N = 100

    gamma = [0.5, 1.0, 2.5]
    Vgs = [0.0, 10.0]
    
    def __init__(self):
        """
        Constructs a Yampex Plotter object for a figure with two subplots.
        """
        self.pt = Plotter(2, width=self.width, height=self.height)
        self.pt.use_grid()

    def n(self, gamma, Vgs, Tj=25):
        """
        The function for n:

        M{n = 1+gamma/(-gamma+2*sqrt(gamma^2/4 + Vgs + 1.10/300*(Tj+273.15)))}
        """
        T = Tj + 273.15
        n = gamma.copy() # Otherwise we wind up modifying gamma
        n /= -gamma + 2*np.sqrt(gamma**2/4 + Vgs + 1.1/300*T)
        n += 1
        return n

    def subplot(self, sp, X, aVals, bVals, semilog=False):
        """
        Given the subplotting tool I{sp} and the supplied 1-D Numpy array
        of I{X} values, plots the curves for each combination of I{a}
        in I{aVals} and I{b} in I{bVals}.
        """
        Ys = []
        for a, b in zip(aVals, bVals):
            Ys.append(self.func(X, a, b))
            sp.add_legend("a={:.2f}, b={:.2f}", a, b)
        if semilog:
            sp.semilogy(X, *Ys)
        else: sp(X, *Ys)
                
    def plot(self):
        """
        Plots the curves for each combination of I{a} in I{aVals} and its
        corresponding I{b} in I{bVals}, from my I{xMin} to my I{xMax}
        and from zero to double my I{xMax}.
        """
        self.pt.set_ylabel("n")
        with self.pt as sp:
            sp.set_title("n vs gamma with stepped Vgs")
            sp.set_xlabel("gamma")
            ax = sp()
            gamma = np.linspace(self.gamma[0], self.gamma[1], self.N)
            for Vgs in np.linspace(self.Vgs[0], self.Vgs[1], 5):
                with sp.prevOpts():
                    sp.add_legend("Vgs: {:.1f}", Vgs)
                n = self.n(gamma, Vgs)
                ax.plot(gamma, n)
            sp.set_title("n vs Vgs with stepped gamma")
            sp.set_xlabel("Vgs")
            ax = sp()
            Vgs = np.linspace(self.Vgs[0], self.Vgs[1], self.N)
            for gamma in np.linspace(self.gamma[0], self.gamma[1], 5):
                with sp.prevOpts():
                    sp.add_legend("gamma: {:.1f}", gamma)
                n = self.n(gamma, Vgs)
                ax.plot(Vgs, n)
        self.pt.show()


def run():
    # Plot the curves
    CurvePlotter().plot()


if __name__ == '__main__':
    run()
