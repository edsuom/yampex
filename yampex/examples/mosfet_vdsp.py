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


class MOSFET(object):
    """
    I model a few aspects of an N-channel MOSFET.
    """
    # Nominal (room) temperature (K)
    Tr = 300
    # Boltzmann's constant
    k = 1.38064853e-23
    # Electron charge
    q = 1.60217663e-19
    # Bandgap energy of silicon (V), from Ravindra & Srivastava
    # (1979).
    Eg = 1.111
    # Intrinsic carrier concentration of Si
    ni = 1.015e10
    # Electron affinity of Si (V), T&M p. 28.
    Chi = 4.05
    # Permittivity of free space
    e0 = 8.854e-16 # F/m
    # Dielectric constant of silicon and silicon dioxide
    ks = 11.9; kso2 = 3.9
    # Interface charge density (C/cm^2). Roughly midrange guess from
    # T&M pp. 70-71, set to Example 2.2 value.
    Qd0 = 1e-8

    def __init__(self, tox, NA, ND=1e19):
        self.tox = tox
        self.NA = NA
        self.ND = ND
        self.Pt = self.k*self.Tr/self.q

    def __repr__(self):
        return sub("tox={:.5g}, NA={:.5g}", self.tox, self.NA)
        
    @property
    def Cdox(self):
        """
        Oxide capacitance per unit area (F/cm^2).
        """
        eox = self.kso2 * self.e0
        return eox / self.tox

    @property
    def PF(self):
        """
        Substrate (bulk) Fermi potential PF (phi_F) at nominal
        temperature.
        """
        return self.Pt*np.log(self.NA/self.ni)

    @property
    def Vfb(self):
        """
        Flatband voltage.
        """
        PMS = -self.Pt*np.log(self.ND/self.ni) - self.PF
        return PMS - (self.Qd0 / self.Cdox)

    @property
    def gamma(self):
        """
        Body effect coefficient.
        """
        # Permittivity of silicon
        es = self.e0 * self.ks
        # Gamma
        return np.sqrt(2*self.q*es*self.NA) / self.Cdox

    @property
    def VT(self):
        """
        Threshold voltage.
        """
        P0 = 2*self.PF + 6*self.Pt
        return self.Vfb + P0 + self.gamma*np.sqrt(P0)
    
    def n(self, Vgs):
        """
        Given I{Vgs}, returns I{n}, the inverse of the first derivative of
        the surface potential deep in depletion vs Vgs.
        """
        gamma = self.gamma
        denom = -gamma + 2*np.sqrt(gamma**2/4 + Vgs - self.Vfb)
        return 1 + (gamma / denom)


class CurvePlotter(object):
    """
    I do the plotting.
    """
    N = 100
    width = 1400
    height = 1400

    Vgs = [0.0, 10.0]
    
    def __init__(self):
        """
        Constructs a Yampex Plotter object for a figure with two subplots.
        """
        self.mList = []
        # Small MOSFET in an IC
        self.mList.append(MOSFET(2.5e-9, 5e17))
        # High-current Power MOSFET
        self.mList.append(MOSFET(4e-9, 2.7e19))
        # Plotter
        self.N_sp = len(self.mList)
        self.pt = Plotter(self.N_sp, width=self.width, height=self.height)
        self.pt.use_grid()
        self.pt.set_xlabel("Vgst")
        self.pt.set_ylabel("Vdsp")
        self.pt.add_legend("Vgst/n")
        self.pt.add_legend("(Vgst-f(x))/n")
        self.pt.use_labels()

    def Vdsp_1(self, m, Vgs):
        Vgst = Vgs - m.VT
        return Vgst/m.n(Vgs)

    def Vdsp_2(self, m, Vgs, x=0.1):
        Vgst = Vgs - m.VT
        n = m.n(Vgs); Pt = m.Pt
        second = 2*n*Pt*np.log((1 + np.exp(Vgst/(2*n*Pt)))**np.sqrt(x) - 1)
        return (Vgst - second) / n
    
    def plot(self):
        """
        """
        with self.pt as sp:
            for m in self.mList:
                sp.set_title("Vdsp vs Vgst, computed both ways, for {}", m)
                Vgs = np.linspace(self.Vgs[0], self.Vgs[1], 100)
                #sp(Vgs, self.Vdsp_1(m, Vgs), self.Vdsp_2(m, Vgs))
                sp(Vgs, self.Vdsp_2(m, Vgs))
        self.pt.show()


def run():
    # Plot the curves
    CurvePlotter().plot()


if __name__ == '__main__':
    run()
