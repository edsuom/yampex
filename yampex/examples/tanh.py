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
Plots of a primitive MOSFET drain current versus drain-to-source
voltage model.

The model (it's actually a Numpy prototype of a much larger model for
another project of mine) sums M{a[k]*tanh(b[k]*x)} for several
I{k}. This example shows the total current with a solid line and the
current of each component with dotted lines.

There are two subplots, a top one for the drain current vs voltage and
another for the effective resistance (dV/dI) vs current.

Illustrates line colors and styles and legends, and the seamless use
of object-oriented programming with Yampex.
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
        return len(self.ab)
        
    def clear(self):
        """
        Clears my model of all M{a*tanh(b*v)} components.
        """
        self.ab = []

    def addComponent(self, a, b):
        """
        Adds a M{a*tanh(b*v)} component to my summation (parallel current
        paths) model.
        """
        self.ab.append([a, b])

    def currents(self):
        """
        Returns a list of 1-D Numpy vectors to plot.

        The first two vectors in the list are (1) Vds and (2) the
        total Ids at each Vds value. The vectors following are the
        contributions of each M{a*tanh(b*v)} component to the total
        Ids.
        """
        Vs = [self.Vds, 0]
        for a, b in self.ab:
            Ids = a*np.tanh(b*self.Vds)
            Vs[1] += Ids
            Vs.append(Ids)
        return Vs

    def resistance(self, Id):
        """
        Returns the effective resistance of whatever produced drain
        current (or contribution to drain current) I{Id} at each value
        of my swept drain voltage I{Vds}.
        """
        return self.Vds / Id

    def labelerator(self):
        """
        Generates text of a label for each of my components.
        """
        for a, b in self.ab:
            yield sub("{:.1f}*tanh({:.1f}*Vds)", a, b)
        

class CurvePlotter(object):
    """
    I do the plotting.
    """
    width = 1200
    height = 1000
    def __init__(self):
        """
        Constructs a Yampex Plotter object for a figure with a two subplots.
        """
        pt = self.pt = Plotter(2, width=self.width, height=self.height)
        pt.use_grid()
        # Add line styles for the total and for each component
        pt.add_line('-', ':')
        # Start with a legend for the total
        pt.add_legend("Overall Model")
        # Use annotation labels insead of a legend, since the legend
        # box tends to get in the way
        pt.use_labels()

    def plot(self, m):
        """
        Plots the curves for the supplied instance I{m} of L{Model}.
        """
        self.pt.set_title(
            "DC MOSFET Model with fixed Vgs and {:d} parallel current paths",
            len(m))
        for label in m.labelerator():
            self.pt.add_legend(label)
        with self.pt as sp:
            sp.set_xlabel("Vds"); sp.set_ylabel("Ids")
            Vs = m.currents()
            sp(*Vs)
            Rs = [m.resistance(Ids) for Ids in Vs[1:]]
            sp.set_xlabel("Ids"); sp.set_ylabel("Rds")
            sp.semilogy(Vs[1], *Rs)
        self.pt.show()


def run():
    # The model
    m = Model(20, 10.0)
    # Define the model components
    m.addComponent(1.0, 0.3)
    m.addComponent(1.5, 0.7)
    m.addComponent(2.5, 1.0)
    # Plot the model
    CurvePlotter().plot(m)


if __name__ == '__main__':
    run()
