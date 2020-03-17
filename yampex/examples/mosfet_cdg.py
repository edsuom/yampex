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
    height = 1200
    N = 200
    
    def __init__(self):
        """
        Constructs a Yampex Plotter object for a figure with one subplot.
        """
        self.pt = Plotter(1, width=self.width, height=self.height)
        self.pt.use_grid()

    def eta(self, Vds, smooth=False):
        if smooth:
            eta = 0.05*np.log(1 + np.exp(20*(1-Vds)))
        else: eta = np.clip(1 - Vds, 0, None)
        return eta
        
    def Cdg(self, eta):
        """
        The function for Cdg::
        
            Cdg = W*L*Cdox*(4+28*eta+22*eta^2+6*eta^3)/(15*(1+eta)^3)

        """
        result = 4 + 28*eta + 22*eta**2 + 6*eta**3
        return result/(15*(1+eta)**3)

    def plot(self):
        """
        Plots the curve for Cdg vs Vds, given Vds_prime = 1.
        """
        self.pt.set_ylabel("Cdg")
        with self.pt as sp:
            sp.set_title("Cdg vs Vds")
            sp.set_xlabel("Vds")
            Vds = np.linspace(0, 2, self.N)
            eta = self.eta(Vds, True)
            Cdg = self.Cdg(eta)
            ax = sp(Vds, eta, Cdg)
        self.pt.show()


def run():
    # Plot the curves
    CurvePlotter().plot()


if __name__ == '__main__':
    run()
