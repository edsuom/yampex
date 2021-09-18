#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# yampex:
# Yet Another Matplotlib Extension
#
# Copyright (C) 2017-2021 by Edwin A. Suominen,
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

import numpy as np
import matplotlib.gridspec as gridspec

from yampex.helper import PlotHelper
from yampex.util import *


class SpecialAx(object):
    """
    I pretend to be the C{matplotlib.Axes} that I'm constructed with
    except that I intercept plotting calls and have a few extra
    methods.
    
    The plotting calls are intercepted with a wrapper function and
    stored up in my L{PlotHelper} where they can be processed all at
    once. The processing does the following:

        - Rescales the independent vector(s) if they are for time and
          there's a time unit (e.g., nanoseconds) scaling them.

        - Replace C{container, *names} args with vectors in that
          container.

        - Plot with the next line style, marker style, and color if
          not specified in the call.

        - Applies legends and annotations.

    Construct me with a subplot axes object I{ax}, an instance of
    L{Plotter} I{p}, and my integer subplot number (starts with
    1). Or, construct me with an instance of L{PlotHelper}.

    If your call to a L{Plotter} instance (most likely in a subplot
    context) has a container object as its first argument, I will
    replace the arguments with actual Numpy vectors element-wise
    accessed from that container object. The underlying Matplotlib
    call will only see the Numpy vectors. For example,::

        import numpy as np
        V = {'x': np.linspace(0, 1, 100)}
        V['y'] = V['x']**2
        with Plotter(1) as sp:
            sp(V, 'x', 'y')

    will plot the square of I{x} vs I{x}. This comes in handy when you
    have containers full of vectors and you want to plot selected ones
    of them in different subplots.

    @ivar helper: An instance of L{PlotHelper} dedicated to helping
        with my subplot. I either create a new instance or re-use one
        supplied to my constructor.
    """
    __slots__ = ['helper']
    
    def __init__(self, *args):
        """C{SpecialAx(ax, p, kSubplot)} or C{SpecialAx(helper)}"""
        if len(args) == 1:
            self.helper = args[0]
        else: self.helper = PlotHelper(*args)

    @property
    def ax(self):
        """
        Property: Access the underlying Matplotlib C{Axes} object
        directly.
        """
        return self.helper.ax
        
    def __getattr__(self, name):
        """
        Returns a plotting method of my I{_ax} object, wrapped in a
        wrapper function, or the attribute of I{_ax} directly for
        anything else.

        The wrapper looks up vector names from my vector container
        I{V} (if it's not a C{None} object), or from the first arg if
        that is a vector container, applies per-plot keywords if not
        specified in the call, and does x-axis scaling.
        """
        def wrapper(*args, **kw):
            kw['plotter'] = name
            self.helper.addCall(args, kw)
            return self
        x = getattr(self.helper.ax, name)
        return wrapper if name in PLOTTER_NAMES else x


class Subplotter(object):
    """
    I handle your subplots, boundary setting and ticks. A L{Plotter}
    instance constructs me with a reference to itself and an integer
    number of columns and rows.

    If you want one row (or multiple rows) to have twice the height of
    normal rows, supply its index in a sequence or set with the I{h2}
    constructor keyword. Similarly, if you want one column (or
    multiple columns) to have twice the width of normal columns,
    supply its index in a sequence or set with the I{w2} constructor
    keyword.

    This is a convenient way to put emphasis on one or some subplots
    without making things overly complicated. And if you think you
    need a subplot to be more than twice as high or wide as the
    others, think again; your figure would look terrible.

    B{TODO}: Support axis twinning, and a subplot spanning multple
    columns in one row.

    @ivar p: An instance of L{Plotter} that handles all subplots in a
        Matplotlib C{Figure}.
    
    @ivar N: Number of subplots (no greater than Nc*Nr).
    
    @ivar Nc: Number of columns.
    
    @ivar Nr: Number of rows.

    @keyword h2: A single index, or a sequence or set containing one
        or more indices, of any rows (starting with 0 for the top row)
        that have twice the normal height. If an invalid index is
        included, an exception will be raised.

    @keyword w2: A single index, or a sequence or set containing one
        or more indices, of any columns (starting with 0 for the left
        column) that have twice the normal width. If an invalid index
        is included, an exception will be raised.
    """
    def __init__(self, plotter, N, Nc, Nr, h2=None, w2=None):
        if N > Nc*Nr:
            raise ValueError("Number of subplots must be <= Nc*Nr")
        self.p = plotter
        self.N, self.Nc, self.Nr = N, Nc, Nr
        self.axes = []
        kw = {'figure': plotter.fig}
        kw['width_ratios'] = self._doublings('column', w2, Nc)
        kw['height_ratios'] = self._doublings('row', h2, Nr)
        self.gs = gridspec.GridSpec(Nr, Nc, **kw)

    def _doublings(self, which, seqset, N):
        ratios = np.ones(N)
        if seqset is None:
            return ratios
        if isinstance(seqset, int):
            seqset = [seqset]
        seqset = set(seqset)
        if seqset:
            kMax = max(seqset)
            if kMax >= N:
                raise ValueError(
                    sub("Invalid {} index {:d} for {:d} {}s",
                        which, kMax, N, which))
        for k in seqset:
            ratios[k] = 2
        return ratios
        
    def setup(self):
        """
        Clears the figure and sets up a new set of subplots.
        """
        self.axes = []
        self.twins = {}
        self.kLast = None
        self.p.fig.clear()
        for k in range(self.Nc*self.Nr):
            ky, kx = divmod(k, self.Nc)
            ax = self.p.fig.add_subplot(self.gs[ky, kx])
            ax = SpecialAx(ax, self.p, k)
            self.axes.append(ax)
            if k == self.N-1: break
        for ax in self.axes:
            ax.clear()
            for axTwin in self.getTwins(ax, mplRoster=True):
                axTwin.clear()
            if ax in self.twins:
                self.twins[ax][0] = 0

    @property
    def ax(self):
        """
        The C{Axes} object for the current subplot.
        """
        if self.kLast is not None and self.kLast < len(self.axes):
            return self.axes[self.kLast]

    def __iter__(self):
        """
        I can iterate over the C{Axes} objects of subplots I've generated
        so far.
        """
        for ax in self.axes:
            yield ax
        
    def __len__(self):
        """
        My length is the number of subplots I've generated so far.
        """
        return len(self.axes)

    def __getitem__(self, k):
        """
        Returns the C{Axes} object for my subplot with index I{k}, or the
        current one if I{k} is C{None}.
        """
        if k is None:
            k = 0 if self.kLast is None else self.kLast + 1
        self.kLast = k
        if k < len(self.axes):
            return self.axes[k]
    
    def set_(self, what, name, **kw):
        """
        Performs a C{set_} call on my last-generated subplot, where the
        first argument I{what} is the suffix to the underlying "set_"
        method and I{name} is what is being set.

        Any keywords to the setter method can be supplied.

        Returns the result of the setter method call.
        """
        f = getattr(self.ax, "set_{}".format(what))
        return f(name, **kw)

    def xBounds(self, ax=None, left=None, right=None):
        """
        """
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
        Creates and returns a twin of the last (or supplied) axes object.
        
        Maintains a list of the twinned axes in the order they were
        created along with an index of the latest-created twin (for
        axes re-use).

        B{TODO}: Not yet supported!
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
            axTwin = SpecialAx(ax.helper)
            twinList.append(axTwin)
        twin = twinList[k]
        self.twins[ax][0] = k+1
        return twin

    def getTwins(self, ax=None, mplRoster=False):
        """
        Returns a list of the twins for the last (or supplied) axes
        object, starting with the axes object itself and then the
        twins in the order they were created.

        B{TODO}: Twinned axes are not yet supported! Always returns a
        single-element list.
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
        has a sub-dict that may include 'major' and 'minor' entries.

        Each entry, if present, defines the tick intervals. It can
        have one of four forms:

            1. An C{int} for a max number of tick intervals.

            2. A C{float} for spacing between intervals.

            3. A C{Bool}, just C{True} or C{False} to enable or
               disable ticks. (Major ticks are always enabled.)

            4. A 2-sequence of floats containing (1) the spacing
               between intervals and (2) an anchor point that must
               have a tick, i.e., the starting point of intervals with
               ticks below and above it.
        """
        def get(axisName, name):
            return ticksDict.get(optkey(axisName, name), None)

        def locations(axisName, spacing):
            spacing, anchor = spacing
            low, high = self.ax.helper.pairs.minmax(axisName=='y')
            locs = [anchor]
            # Below anchor
            loc = anchor - spacing
            while loc >= low:
                locs.insert(0, loc)
                loc -= spacing
            # Above anchor
            loc = anchor + spacing
            while loc <= high:
                locs.append(loc)
                loc += spacing
            return locs
        
        def setSpacing(axisName, which, spacing):
            axis = getattr(ax, sub("{}axis", axisName))
            setter = getattr(axis, sub("set_{}_locator", which))
            if isinstance(spacing, int):
                locator = self.ticker.MaxNLocator(spacing)
            elif hasattr(spacing, '__iter__'):
                if len(spacing) != 2:
                    raise ValueError(
                        "Tick spacing (interval, anchor) requires 2 elements!")
                locator = self.ticker.FixedLocator(
                    locations(axisName, spacing))
            else: locator = self.ticker.MultipleLocator(spacing)
            setter(locator)

        if ax is None: ax = self.ax
        if not hasattr(self, 'ticker'):
            self.ticker = importlib.import_module("matplotlib.ticker")
        for axisName in 'x', 'y':
            for which in 'major', 'minor':
                spacing = get(axisName, which)
                if spacing is True:
                    if which == 'minor':
                        ax.minorticks_on()
                    # What about major ticks?
                    continue
                elif spacing is False:
                    if which == 'minor':
                        ax.minorticks_off()
                    # What about major ticks?
                    continue
                elif spacing is None:
                    continue
                setSpacing(axisName, which, spacing)

    def kFix(self, k=None):
        """
        If subplot index I{k} is C{None}, returns the index of the current
        subplot, or the first one if there is not yet a current one.

        Does not actually adjust I{kLast}, just the returned value.
        
        Returns the (possibly) fixed subplot index.

        I{TODO}: Fix this for use outside just the internal methods
        below.
        """
        if k is None:
            k = 0 if self.kLast is None else self.kLast
        return k
                
    def onTop(self, k=None):
        """
        Returns C{True} if the current subplot (or one specified with a
        subplot index I{k}) will appear at the top of a column of
        subplots.

        If there is just one subplot or one row of subplots, of course
        this will return C{True}.
        """
        if self.Nr == 1: return True
        return self.kFix(k) < self.Nc
                
    def atBottom(self, k=None):
        """
        Returns C{True} if the current subplot (or one specified with a
        subplot index I{k}) will appear at the bottom of a column of
        subplots.

        If there is just one subplot or one row of subplots, of course
        this will return C{True}.
        """
        if self.Nr == 1: return True
        return self.kFix(k) >= self.Nc * (self.Nr - 1)
    
    def onLeft(self, k=None):
        """
        Returns C{True} if the current subplot (or one specified with a
        subplot index I{k}) will appear in the leftmost column of
        subplots.

        If there is just one subplot or one column of subplots, of
        course this will return C{True}.
        """
        if self.Nc == 1: return True
        return self.kFix(k) % self.Nr == 0
