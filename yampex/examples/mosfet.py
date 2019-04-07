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
Plots of a simple MOSFET model for drain current versus
drain-to-source voltage.

The model (it's actually a Numpy prototype of a much larger model for
another project of mine) sums the drain current of multiple MOSFET
primitives that use the Schichman-Hodges quadratic equations. This
example shows the total current with a solid line and the current of
each component with dotted lines.

There are two subplots, a top one for the drain current vs voltage and
another for the effective resistance (dV/dI) vs current.

Illustrates line colors and styles, annotation-label legends, and the
seamless use of object-oriented programming with Yampex.
"""

import numpy as np
from yampex import Plotter
from yampex.util import sub


class Model(object):
    """
    I implement a primitive DC model of a MOSFET operating at some
    fixed unknown value of Vgs (gate-source voltage).

    Construct an instance of me with the number of points I{N} to plot
    and the maximum I{Vmax} drain-source voltage to sweep up to from
    zero.

    @ivar Vds: My swept drain-source voltage from near (but not at)
        zero to I{Vmax}.
    """
    def __init__(self, N, Vmax):
        self.Vds = np.linspace(0, Vmax, N+1)[1:]
        self.clear()

    def __len__(self):
        """
        My length is the number of components in my summation model.
        """
        return len(self.params)
        
    def clear(self):
        """
        Clears my model of all MOSFET primitive components.
        """
        self.params = []

    def add(self, kp, lamb, vto):
        """
        Adds a MOSFET primitive component to my summation (parallel
        current paths) model.
        """
        self.params.append((kp, lamb, vto))

    def Ids(self, Vgs, kp, lamb, vto):
        """
        Returns a 1-D Numpy vector of drain current through a MOSFET
        primitive at my I{Vds} values, given I{Vgs} and the specified
        I{kp}, I{lamb}da, and I{vto} parameter values.
        """
        # Cutoff
        if Vgs < vto: return np.zeros_like(self.Vds)
        # Linear or Saturation
        which = [0 if x < Vgs - vto else 1 for x in self.Vds]
        L = (Vgs-vto)*self.Vds - 0.5*self.Vds**2
        S = 0.5*((Vgs-vto)**2)*np.ones_like(self.Vds)
        return np.choose(which, [L, S])*kp*(1+lamb*self.Vds)
        
    def currents(self, Vgs):
        """
        Returns a list of 1-D Numpy vectors to plot.

        The first two vectors in the list are (1) Vds and (2) the
        total Idss at each Vds value. The vectors following are the
        contributions of each MOSFET primitive component to the total
        Ids.
        """
        Vs = [self.Vds, 0]
        for kp, lamb, vto in self.params:
            Ids = self.Ids(Vgs, kp, lamb, vto)
            Vs[1] += Ids
            Vs.append(Ids)
        return Vs

    def labelerator(self):
        """
        Generates text of a label for each of my components.
        """
        for kp, lamb, vto in self.params:
            yield sub("kp={:.1f}, lambda={:.2f}, vto={:.1f}", kp, lamb, vto)


class CurvePlotter(object):
    """
    I do the plotting.
    """
    width = 1400
    height = 970
    Ids_max_for_Rds = 80.0
    
    def __init__(self, m):
        """
        Constructs a Yampex Plotter object for a figure with a two
        subplots using the supplied instance I{m} of L{Model}
        """
        self.m = m
        pt = self.pt = Plotter(2, width=self.width, height=self.height)
        pt.use_grid()
        # Add line styles for the total and for each component
        pt.add_line('-', '-.')
        # Start with a legend for the total
        pt.add_legend("Overall Model")
        # Custom colors
        pt.set_colors('blue', 'blue', 'red', 'green')
        # Legend
        for label in m.labelerator():
            pt.add_legend(label)

    def plot(self, Vgs):
        """
        Plots the curves with the specified gate-source voltage I{Vgs}.
        """
        with self.pt as sp:
            sp.set_xlabel("Vds"); sp.set_ylabel("Ids")
            Vs = self.m.currents(Vgs)
            sp(*Vs)
            Ids = Vs[1]
            K = np.flatnonzero(np.logical_and(
                np.greater(Ids, 0), np.less(Ids, self.Ids_max_for_Rds)))
            Vds = self.m.Vds[K]
            sp.set_xlabel("Ids"); sp.set_ylabel("Rds")
            sp(Ids[K], Vds/Ids[K])
        self.pt.show()


def run():
    # Gate-source voltage Vgs
    Vgs = 7.0
    # The model
    m = Model(500, 12.0)
    # Define the model components
    #     kp, lambda, vto
    m.add(2.2, 0.093, 3.54)
    m.add(30.75, 0.188, 5.12)
    m.add(100.48, 0.270, 6.0)
    # Plot the model
    CurvePlotter(m).plot(Vgs)


if __name__ == '__main__':
    run()
