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
Simple subplotting.
"""

import importlib

from yampex.util import sub


class Subplotter(object):
    """
    """
    def __init__(self, plotter, Nx, Ny):
        self.p = plotter
        self.Nx, self.Ny = Nx, Ny
        self.axes = []

    def setup(self):
        """
        Clears the figure and sets up a new set of subplots.
        """
        self.axes = []
        self.twins = {}
        self.kLast = None
        self.p.fig.clear()
        for k in range(self.Nx * self.Ny):
            ax = self.p.fig.add_subplot(self.Ny, self.Nx, k+1)
            self.axes.append(ax)
        for ax in self.axes:
            ax.clear()
            for axTwin in self.getTwins(ax, mplRoster=True):
                axTwin.clear()
            if ax in self.twins:
                self.twins[ax][0] = 0

    @property
    def ax(self):
        if self.kLast is not None and self.kLast < len(self.axes):
            return self.axes[self.kLast]
        
    def __len__(self):
        return len(self.axes)

    def __getitem__(self, k):
        if k is None:
            k = 0 if self.kLast is None else self.kLast + 1
        self.kLast = k
        if k < len(self.axes):
            return self.axes[k]
    
    def set_(self, what, name, **kw):
        f = getattr(self.ax, "set_{}".format(what))
        f(name, **kw)

    def xBounds(self, ax=None, left=None, right=None):
        if ax is None: ax = self.ax
        if left and left < ax.get_xlim()[0]:
            ax.set_xlim(left=left)
        if right and right > ax.get_xlim()[1]:
            ax.set_xlim(right=right)
            
    def yBounds(self, ax=None, Ymax=None, bump=False, zeroBottom=False):
        """
        If I{bump} is C{True} or I{Ymax} is a value greater than 95% of
        the largest y-value currently plotted, increases the upper
        bound by 20%. If I{zeroBottom} is set C{True}, anchors the
        bottom to zero.
        """
        def top(ax):
            return ax.get_ylim()[1]
        
        def updateYlim(ax):
            kw = {}
            if zeroBottom: kw['bottom'] = 0
            if bump: kw['top'] = 1.2*top(ax)
            ax.set_ylim(**kw)
        
        if ax is None: ax = self.ax
        if not bump:
            if Ymax is None:
                lines = ax.get_lines()
                if not lines:
                    return
                Ymax = max([max(x.get_ydata(orig=True)) for x in lines])
            if Ymax > 0.95 * top(ax):
                bump = True
        if zeroBottom or bump:
            for axThis in self.getTwins(ax):
                updateYlim(axThis)

    def twinx(self, ax=None):
        """
        Creates and returns a twin of the last (or supplied) axes object,
        maintaining a list of the twinned axes in the order they were
        created along with an index of the latest-created twin (for
        axes re-use).
        """
        if ax is None: ax = self.ax
        # Shouldn't need redundant storage from what MatplotLib does,
        # but whatever
        if ax in self.twins:
            k, twinList = self.twins[ax]
        else:
            k = 0
            twinList = []
            self.twins[ax] = [k, twinList]
        if k >= len(twinList):
            twinList.append(ax.twinx())
        twin = twinList[k]
        self.twins[ax][0] = k+1
        return twin

    def getTwins(self, ax=None, mplRoster=False):
        """
        Returns a list of the twins for the last (or supplied) axes
        object, starting with the axes object itself and then the
        twins in the order they were created.
        """
        if ax is None: ax = self.ax
        if mplRoster:
            # API hint to Matplotlib devs: Don't unecessarily nest lists!
            groupAsList = list(ax.get_shared_x_axes())
            return groupAsList[0] if groupAsList else []
        twins = [ax]
        if ax in self.twins:
            k, twinList = self.twins[ax]
            twins.extend(twinList[:k])
        return twins

    def setTicks(self, ticksDict, ax=None):
        """
        Call with a dict defining ticks for 'x' and 'y' axes. Each axis
        has a sub-dict with 'major' and 'minor' entries. Each entry,
        if present, is an C{int} for a max number of tick intervals,
        or a C{float} for spacing between intervals, or just C{True}
        or C{False} to enable or disable ticks. (Major ticks are
        always enabled.)
        """
        def get(axisName, name):
            return ticksDict.get(axisName, {}).get(name, None)
        
        def setSpacing(which):
            setter = getattr(axis, sub("set_{}_locator", which))
            if isinstance(spacing, int):
                setter(self.ticker.MaxNLocator(spacing))
            else: setter(self.ticker.MultipleLocator(spacing))
        
        if ax is None: ax = self.ax
        if not hasattr(self, 'ticker'):
            self.ticker = importlib.import_module("matplotlib.ticker")
        for axisName in 'x', 'y':
            axis = getattr(ax, sub("{}axis", axisName))
            for which in 'major', 'minor':
                spacing = get(axisName, which)
                if spacing is True:
                    if which == 'minor': ax.minorticks_on()
                elif spacing is False:
                    if which == 'minor': ax.minorticks_off()
                elif spacing is None:
                    continue
                setSpacing(which)

    def atBottom(self):
        """
        Returns C{True] if the current subplot will appear at the bottom
        of a column of subplots.
        """
        k = 0 if self.kLast is None else self.kLast
        return (k+1) % self.Ny == 0
    
