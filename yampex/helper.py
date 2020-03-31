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
You'll do everything with a L{Plotter} in context.

Keep the API for its L{OptsBase} base class handy, and maybe a copy of
its U{source<http://edsuom.com/yampex/yampex.options.py>}, to see all
the plotting options you can set.
"""


import numpy as np

from yampex.annotate import Annotator
from yampex.textbox import TextBoxMaker
from yampex.util import sub, PLOTTER_NAMES


class Pair(object):
    """
    I represent the information for one X, Y pair of vectors in a
    plotting call.

    @ivar call: The call name, 'plot', 'bar', etc.
    
    @ivar X: The independent (x-axis) vector.

    @ivar Xname: The name of the I{X} vector, of C{None} if no name
        was defined.
    
    @ivar Y: The dependent (y-axis) vector.
    
    @ivar Yname: The name of the I{Y} vector, of C{None} if no name
        was defined.
    
    @ivar fmt: A string-type line/markers/color formatting argument,
        or a blank string if no such argument was supplied.

    @ivar kw: Any keywords supplied for the call, shared with one or
        more other instances of me if there was more than one
        dependent vector in the call.
    """
    __slots__ = ['call', 'X', 'Xname', 'Y', 'Yname', 'fmt', 'kw']

    def sameX(self, X):
        """
        Returns C{True} if the supplied vector I{X} is, or is a duplicate
        of, my independent vector I{X}.
        """
        if X is self.X: return True
        if X.shape != self.X.shape: return False
        return np.all(np.equal(X, self.X))

    def getXY(self, asArray=False):
        """
        Returns my I{X} and I{Y} vectors.

        @keyword asArray: C{True} to get the vectors as a 2D Numpy
            array.
        """
        if asArray:
            return np.column_stack([self.X, self.Y])
        return self.X, self.Y
        

class Pairs(list):
    """
    A slightly improved C{list} for holding L{Pair} objects.
    """
    def copy(self):
        np = Pairs()
        for item in self:
            np.append(item)
        return np
    
    def getXY(self, k, asArray=False):
        """
        Returns the I{X} and I{Y} vectors of the L{Pair} at index I{k}.

        @keyword asArray: C{True} to get the vectors as a 2D Numpy
            array.
        """
        return self[k].getXY(asArray)

    def firstX(self):
        """
        Returns the Numpy array and name of the very first x-axis vector
        added to me (possibly the only one). If no vectors have been
        added yet, returns C{None}, C{None}.
        """
        if self:
            firstPair = self[0]
            return firstPair.X, firstPair.Xname
        return None, None
    
    def minmax(self, useY=False):
        """
        Returns the lowest and highest values found in any of my pairs'
        x-axis vectors, unless I{useY} is C{True}, in which their
        y-axis vectors are looked at instead.

        Empty vectors are disregarded. If I have no pairs yet or only
        pairs with an empty vector of interest, returns C{None} for
        both.
        """
        minmax = [None, None]
        for pair in self:
            Z = pair.Y if useY else pair.X
            if not len(Z): continue
            # Min
            prev = minmax[0]
            value = Z.min()
            if prev is None or value < prev:
                minmax[0] = value
            # Max
            prev = minmax[1]
            value = Z.max()
            if prev is None or value > prev:
                minmax[1] = value
        return minmax

    def scaleX(self, scale):
        """
        Multiplies the x-axis vector of each of my pairs by the specified
        I{scale}.
        """
        if not scale or scale == 1: return
        for pair in self:
            # Can't do 'pair.X *= scale' for Ngspice compatibility in
            # another project
            pair.X = scale * pair.X


class PlotHelper(object):
    """
    I help with plotting calls for a single subplot.

    @ivar ax: The first and possibly only Matplotlib C{Axes} object
        for the subplot (a real one, not a L{SpecialAx} instance) for
        my subplot. (Will be the only one until twinning is
        supported.)
    
    @ivar pairs: An instance of L{Pairs} containing L{Pair} instances,
        one for each X, Y pair of vectors defined by plotting calls
        made on this subplot. (A single plotting call may define more
        than one X, Y pair.)
    """
    timeScales = [
        (1E-9,          "Nanoseconds"),
        (1E-6,          "Microseconds"),
        (1E-3,          "Milliseconds"),
        (1.0,           "Seconds"),
        (60.0,          "Minutes"),
        (3600.0,        "Hours"),
    ]
    bogusMap = {
        'bar': ('marker', 'linestyle',),
        'step': ('marker', 'linestyle',),
        'errorbar': ('marker', 'linestyle',),
    }
    __slots__ = ['ax', 'p', 'k', 'pairs', 'lineInfo', 'legendIndices']
    
    def __init__(self, ax, p, kSubplot):
        self.ax = ax
        self.p = p
        self.k = kSubplot
        self.pairs = Pairs()
        self.lineInfo = [[], []]
        self.legendIndices = []

    def __getattr__(self, name):
        """
        You can access any of my L{Plotter} object's attributes as my own
        whose names don't conflict with those of my own attributes.

        Best to refer to I{p} directly, though. This is a messy crutch.
        """
        return getattr(self.p, name)

    def arrayify(self, V, X):
        """
        Returns the 1-D Numpy array form of I{X}, if possible.

        If I{V} is not C{None} and I{X} is the key of an item in I{V},
        replaces I{X} with that item. Then, if it's not one already,
        converts I{X} to a 1-D Numpy array.

        Returns a 3-tuple with (1) the 1-D Numpy array version of I{X}
        or its original value if it couldn't be converted to one, (2)
        its name or C{None} if it was not an item of I{V}, and (3) a
        boolean C{True} if the result is a Numpy array.
        """
        def isArray(X):
            """
            Returns C{True} if I{X} is a Numpy array or something that can be
            coerced into being one with C{np.array(X)}.
            """
            yes = isinstance(X, (list, tuple, np.ndarray))
            if yes and not isinstance(X, np.ndarray):
                X = np.array(X)
            return yes, X

        yes, X = isArray(X)
        if yes:
            orig = None
        elif hasattr(V, '__contains__'):
            try: isItem = X in V
            except: isItem = False
            if isItem:
                orig = X
                X = V[X]
                yes, X = isArray(X)
            else: orig = None
        else: orig = None
        return X, orig, yes

    def _timeScaling(self, X):
        """
        If the 'timex' option is set C{True}, sets my subplot's x-axis
        scaling to use the most appropriate time multiplier unit and
        sets that unit name as the 'xlabel'.

        Called by L{addCall}, with the current subplot's local options.
        """
        if self.p.opts['timex']:
            T_max = X.max()
            for mult, name in self.timeScales:
                if mult < 1:
                    if T_max < 1000*mult:
                        break
                elif T_max < 150*mult:
                    break
            self.p.opts['xlabel'] = name
            self.p.opts['xscale'] = 1.0 / mult
    
    def addCall(self, args, kw):
        """
        Parses the supplied I{args} into X, Y pairs of vectors, appending
        a L{Pair} object for each to my I{pairs} list.
        
        Pops the first arg and uses it as a container if it is a
        container (e.g., a dict, not a Numpy array). Otherwise, refers
        to the I{V} attribute of my L{Plotter} I{p} as a possible
        container. If there is indeed a container, and the remaining
        args are all strings referencing items that are in it, makes
        the remaining args into vectors.

        Each item of the names list is a string with the name of a
        vector at the same index of I{vectors}, or C{None} if that
        vector was supplied as-is and thus no name name was available.

        Called with the next subplot's local options, so need to
        temporarily switch back to options for the current subplot,
        for the duration of this call.
        """
        def likeArray(X):
            return isinstance(X, (list, tuple, np.ndarray))

        self.p.opts.usePrevLocal()
        args = list(args)
        # The 'plotter' keyword is reserved for Yampex, unrecognized
        # by Matplotlib
        call = kw.pop('plotter', self.p.opts['call'])
        # The 'legend' keyword gets co-opted, but ultimately shows up
        # in the plot like you would expect
        legend = kw.pop('legend', None)
        if legend and not isinstance(legend, (list, tuple)):
            legend = [legend]
        # Process args
        if args and self.p.V is None:
            if likeArray(args[0]):
                V = None
                OK = True
            elif len(args) < 2:
                OK = False
            else:
                V = args.pop(0)
                try: OK = likeArray(V[args[0]])
                except: OK = False
            if not OK:
                raise ValueError(sub(
                    "No instance-wide V container and first "+\
                    "arg {} is not a valid container of a next arg", V))
        else: V = self.p.V
        X0, X0_name = self.pairs.firstX()
        Xs = []
        names = []
        strings = {}
        for k, arg in enumerate(args):
            X, name, isArray = self.arrayify(V, arg)
            if isArray:
                Xs.append(X)
                # A keyword-specified legend overrides any auto-generated name set
                # otherwise
                thisLegend = None
                if legend:
                    if len(args) == 1:
                        thisLegend = legend[0]
                    elif k > 0 and k <= len(legend):
                        thisLegend = legend[k-1]
                if thisLegend:
                    if self.p.opts['autolegend']:
                        name = thisLegend
                    else: self.p.add_legend(thisLegend)
                names.append(name)
            else: strings[k] = X
        if len(Xs) == 1:
            kStart = 0
            # Just one vector supplied...
            if X0 is None:
                # ...and no x-axis range vector yet, so create one
                X0 = np.arange(len(Xs[0]))
                X0_name = None
            # ... but we have an x-axis range vector, so we'll just
            # re-use it
        elif Xs:
            kStart = 1
            # Use this call's x-axis vector
            X = Xs.pop(0)
            # Set time scaling based on this x-axis vector if it's the
            # first one
            if X0 is None: self._timeScaling(X)
            X0 = X; X0_name = names.pop(0)
        # Make pairs with the x-axis vector and the remaining vector(s)
        for k, Y in enumerate(Xs):
            if X0.shape != Y.shape:
                raise ValueError(sub(
                    "Shapes differ for X, Y: {} vs {}", X0.shape, Y.shape))
            pair = Pair()
            pair.call = call
            pair.X = X0
            pair.Xname = X0_name
            pair.Y = Y
            pair.Yname = names[k]
            key = k+kStart+1
            pair.fmt = strings.pop(key) if key in strings else None
            pair.kw = kw
            self.pairs.append(pair)
        self.p.opts.useLastLocal()

    def addLegend(self, kVector, text=None):
        """
        Adds an annotation for a legend, putting it at the right-most
        point where the value is at least 99.9% of the vector maximum
        """
        pair = self.pairs[kVector]
        if not text: text = pair.name
        if not text: return
        if not self.legendIndices:
            Y = pair.Y
            if max(Y) > 0:
                m999 = np.greater(Y, 0.999*max(Y))
            else: m999 = np.less(Y, 0.999*min(Y))
            k = max(np.nonzero(m999)[0])
        else: k = int(np.round(0.7*min(self.legendIndices)))
        self.legendIndices.append(k)
        self.p.annotations.append((k, text, kVector, False))

    def pickPlotter(self, call, kw):
        """
        Returns a reference to the plotting method of my I{ax} object
        named with I{call}, modifying the supplied I{kw} dict in-place
        as needed to work with that call.
        """
        if call in PLOTTER_NAMES:
            func = getattr(self.ax, call, None)
            if func:
                for bogus in self.bogusMap.get(call, []):
                    kw.pop(bogus, None)
            return func
        raise LookupError(sub("No recognized Axes method '{}'", call))
    
    def plotVectors(self):
        """
        Here is where I finally plot my X, Y vector pairs.

        B{TODO:} Support yscale, last seen in commit #e20e6c15. Or
        maybe don't bother.
        """
        for k, pair in enumerate(self.pairs):
            kw = {} if pair.fmt else self.p.doKeywords(k, pair.kw)
            plotter = self.pickPlotter(pair.call, kw)
            # Finally, the actual plotting call
            args = [pair.X, pair.Y]
            if pair.fmt: args.append(pair.fmt)
            self.lineInfo[0].extend(plotter(*args, **kw))
            # Add legend, if selected
            legend = self.p.opts['legend']
            if k < len(legend):
                # We have a legend for this subplot
                legend = legend[k]
            elif self.p.opts['autolegend']:
                # We don't have a legend for the subplot, but
                # autolegend is enabled, so make one up
                legend = pair.Yname
                if not legend: legend = sub("#{:d}", k+1)
            else:
                # We have gone past the last defined legend, or none
                # have been defined
                continue
            self.lineInfo[1].append(legend)
            if self.p.opts['useLabels']: self.addLegend(k, legend)
    
    def addAnnotations(self):
        """
        Creates an L{Annotator} for my annotations to this subplot and
        then populates it.

        Twinned C{Axes} objects in a single subplot are not yet
        supported (and may never be), so the annotator object is
        constructed with my single C{Axes} object and operates only
        with that. That does B{not} mean that only a single vector can
        be annotated within one subplot. Twinning is an unusual use
        case and multiple vectors typically share the same C{Axes}
        object. An annotation can point its arrow to any X,Y
        coordinate in the subplot, whether that is on a plotted curve
        or not.

        This method only adds the annotations, plopping them right on
        top of the data points of interest. You need to call
        L{updateAnnotations} to have them intelligently repositioned
        after the subplot has been completed and its final dimensions
        are established, or (B{TODO}) if it is resized and the
        annotations need repositioning.
        """
        self.p.plt.draw()
        # There will be no twinned axes as that's not yet supported;
        # axList will always contain a single Axes object.
        axList = self.p.sp.getTwins()
        fontsize = self.p.fontsize('annotations', 'small')
        # This one Annotator will take care of all my annotations
        annotator = self.p.annotators[self.ax] = Annotator(
            axList[0], self.pairs, fontsize=fontsize)
        for k, text, kVector, is_yValue in self.p.opts['annotations']:
            X, Y = self.pairs[kVector].getXY()
            if not isinstance(k, int):
                if is_yValue:
                    k = np.argmin(np.abs(Y-k))
                else: k = np.searchsorted(X, k)
            if k < 0 or k >= len(X):
                continue
            x = X[k]; y = Y[k]
            if isinstance(text, int):
                text = sub("{:d}", text)
            elif isinstance(text, float):
                text = sub("{:.2f}", text)
            # Annotator does not yet support twinned axes, nor are
            # they yet used
            annotator.add(x, y, text)

    def updateAnnotations(self):
        """
        Updates the positions of all my annotations.
        """
        plt = self.p.plt
        plt.draw()
        annotator = self.p.annotators[self.ax]
        if annotator.update():
            plt.pause(0.0001)
            plt.draw()
        
    def doPlots(self):
        """
        Does all my plotting and then the follow-up work for it.
        """
        self.p.opts.useLocal(self.k)
        xscale = self.p.opts['xscale']
        self.pairs.scaleX(xscale)
        self.p.doSettings(self.k)
        self.plotVectors()
        Ymin, Ymax = self.pairs.minmax(useY=True)
        axisExact = self.p.opts['axisExact']
        zeroBottom = self.p.opts['zeroBottom']
        # Axis bounds
        if axisExact.get('x', False):
            self.ax.set_xlim(*self.pairs.minmax())
        if axisExact.get('y', False):
            self.ax.set_ylim(Ymin, Ymax)
        elif self.p.opts['bump']:
            self.p.yBounds(
                self.ax, bump=True, zeroBottom=zeroBottom)
        elif self.p.opts['firstVectorTop']:
            self.p.yBounds(ax, Ymax=Ymax, zeroBottom=zeroBottom)
        # Vertical lines
        for axvline in self.p.opts['axvlines']:
            x = None
            if isinstance(axvline, int):
                X0 = self.pairs.firstX()[0]
                if X0 is not None and abs(axvline) < len(X0):
                    x = X0[axvline]
            else: x = axvline
            if x is None: continue
            self.ax.axvline(x=x*xscale, linestyle='--', color="#404040")
        # Zero line (which may be non-zero)
        kw = self.p.opts['zeroLine']
        yz = kw.pop('y', False)
        if yz is True: yz = 0
        if yz is not None and yz is not False:
            y0, y1 = self.ax.get_ylim()
            if y0 < yz and y1 > yz:
                kw['zorder'] = -5
                self.ax.axhline(y=yz, **kw)
        # Legend, if not done with annotations
        if self.p.opts.useLegend():
            self.ax.legend(*self.lineInfo, **{
                'loc': "best",
                'fontsize': self.p.fontsize('legend', "small")})
        self.addAnnotations()
        # Text boxes
        tbs = self.p.opts['textBoxes']
        if tbs:
            tbm = TextBoxMaker(
                self.ax, self.p.Nc, self.p.Nr,
                fontsize=self.p.fontsize('textbox', "small"))
            for quadrant in tbs:
                tbm(quadrant, tbs[quadrant])
        # Decorate the subplot
        ticks = self.p.opts['ticks']
        self.p.sp.setTicks(ticks)
        if self.p.opts['grid']:
            self.ax.grid(True, which='major')
            if ticks.get('x', False) or ticks.get('y', False):
                self.ax.grid(True, which='minor', color='#D0D0D0', linestyle=':')
        self.p.opts.useLastLocal()
        # Have any annotations intelligently repositioned now that the
        # subplot is completed.
        self.updateAnnotations()
