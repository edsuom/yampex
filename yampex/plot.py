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

from copy import deepcopy
import importlib

import numpy as np

from yampex.annotate import Annotator
from yampex.subplot import Subplotter
from yampex.util import sub


class OptsBase(object):
    def set_loglog(self, yes=True):
        self.opts['loglog'] = yes

    def set_semilogx(self, yes=True):
        self.opts['semilogx'] = yes

    def set_semilogy(self, yes=True):
        self.opts['semilogy'] = yes
        
    def set_useLabels(self, yes=True):
        self.opts['useLabels'] = yes

    def set_grid(self, yes=True):
        self.opts['grid'] = yes

    def set_timex(self, yes=True):
        self.opts['timex'] = yes

    def set_firstVectorTop(self):
        self.opts['firstVectorTop'] = True
        
    def set_bump(self, yes=True):
        self.opts['bump'] = yes

    def set_zeroBottom(self, yes=True):
        self.opts['zeroBottom'] = yes

    def add_marker(self, x):
        self.opts['markers'].append(x)

    def add_line(self, x):
        self.opts['linestyles'].append(x)

    def set_yscale(self, x):
        self.opts['yscale'] = x

    def set_axvline(self, x):
        self.opts['axvline'] = x
        
    def set_xlabel(self, x):
        self.opts['xlabel'] = x

    def set_ylabel(self, x):
        self.opts['ylabel'] = x

    def set_legend(self, yes=True):
        self.opts['legend'] = yes
        
    def add_legend(self, proto, *args):
        text = sub(proto, *args)
        self.opts['legend'].append(text)

    def clear_legend(self):
        self.opts['legend'] = []
        
    def clear_annotations(self):
        self.opts['annotations'] = []
        
    def add_annotation(self, k, text, kVector=0):
        self.opts['annotations'].append((k, text, kVector))

    def set_title(self, proto, *args):
        text = sub(proto, *args)
        self.opts['title'] = text


class ContextOpts(object):
    def __init__(self, p):
        self.p = p
        self.opts = {}
        self._refresh()

    def _refresh(self):
        self.merged = self.opts.copy()
        for key in self.p.opts:
            if key not in self.merged:
                self.merged[key] = self.p.opts[key]
        
    def __len__(self):
        self._refresh()
        return len(self.merged)

    def __getitem__(self, name):
        self._refresh()
        return self.merged[name]

    def __setitem__(self, name, value):
        self.opts[name] = value

    def __iter__(self):
        return iter(self.merged)

    def get(self, name, value, default):
        self._refresh()
        return self.merged.get(name, value, default)

    def copy(self):
        self._refresh()
        return self.merged.copy()
    

class SpecialAx(object):
    """
    I pretend to be an L{matplotlib.Axes} object except that I
    intercept plotting calls and rescale the independent vector first.
    """
    _plotterNames = {
        'plot', 'loglog',
        'semilogx', 'semilogy', 'scatter', 'step', 'bar', 'stem'}
    
    def __init__(self, ax, opts, V):
        self.ax = ax
        self.opts = opts
        self.V = V

    def __getattr__(self, name):
        def wrapper(*args, **kw):
            args = list(args)
            if self.V is not None:
                for k, arg in enumerate(args[:2]):
                    if isinstance(arg, str) and arg in self.V:
                        args[k] = self.V[arg]
            if xscale:
                args[0] = args[0] * xscale
            return x(*args, **kw)

        x = getattr(self.ax, name)
        if name not in self._plotterNames:
            return x
        xscale = self.opts.get('xscale', None)
        if xscale or self.V is not None:
            return wrapper
        return x

    
class Plotter(OptsBase):
    """
    I provide a Figure with one or more time-vector and XY subplots of
    Numpy vectors using Matplotlib.

    If you supply an object other than a list or tuple that houses
    vectors and provides access to them by name as items (i.e., a dict
    or a Vectors object from the I{pingspice} package) as a third
    argument, I will convert vector names to vectors for you in each
    plotting call.

    Any keywords you supply to the constructor are used to C{set\_X}
    the axes for all subplots. For example, C{yticks=[1,2,3]} results
    in a C{set\_yticks([1,2,3])} command to the C{axes} object for all
    subplots.
    """
    figSize = (10.0, 7.0)
    colors = ['b', 'g', 'r', '#40C0C0', '#C0C040', '#C040C0', '#8080FF']
    timeScales = [
        (1E-9, "nanoseconds"),
        (1E-6, "microseconds"),
        (1E-3, "milliseconds"),
    ]

    _opts = {
        'marker':               '',
        'linestyle':            '-',
        'markers':              [],
        'linestyles':           [],
        'minorTicks':           [],
        'grid':                 False,
        'firstVectorTop':       False,
        'loglog':               False,
        'semilogx':             False,
        'semilogy':             False,
        'legend':               [],
        'annotations':          [],
        'xscale':               None,
        'yscale':               None,
        'useLabels':            False,
        'axvline':              None,
        'bump':                 False,
        'timex':                False,
        'xlabel':               "",
        'ylabel':               "",
        'title':                "",
        'zeroBottom':           False,
    }
    _settings = {'title', 'xlabel', 'ylabel'}
    _plotters = []
    
    def __init__(self, N, *args, **kw):
        args = list(args)
        if args:
            Nx = N
            Ny = args.pop(0)
        else:
            Nx = self.N_cols(N)
            Ny = int(np.ceil(float(N)/Nx))
        self.V = args[0] if args else None
        self._plotters.append(self)
        self.opts = deepcopy(self._opts)
        self.filePath = kw.pop('filePath', None)
        self.plt = importlib.import_module("matplotlib.pyplot")
        figSize = list(self.figSize)
        if 'width' in kw:
            figSize[0] = kw.pop('width')
        if 'height' in kw:
            figSize[1] = kw.pop('height')
        self.fig = self.plt.figure(figsize=figSize)
        self.sp = Subplotter(self, Nx, Ny)
        self.annotators = {}
        self.kw = kw
        self._isFigTitle = False
        
    def __getattr__(self, name):
        return self.opts[name]
        
    def __enter__(self):
        self.sp.setup()
        self.originalOpts = self.opts.copy()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sp.postOp()
        self.opts = self.originalOpts

    def N_cols(self, N):
        if N > 6:
            return 3
        if N > 3:
            return 2
        return 1

    def figTitle(self, title):
        self.fig.suptitle(title)
        self._isFigTitle = True
    
    def show(self, title=None, subcall=False):
        if not subcall and len(self._plotters) > 1:
            for p in self._plotters:
                p.show(title, subcall=True)
            self.plt.show()
            return
        self.fig.tight_layout()
        if self._isFigTitle:
            self.fig.subplots_adjust(top=0.93)
        self.plt.draw()
        for annotator in self.annotators.values():
            annotator.update()
        if self.filePath is None:
            self.plt.draw()
            if title:
                self.fig.canvas.set_window_title(title)
            if not subcall:
                self.plt.show()
            return
        fh = open(self.filePath, 'wb+')
        self.fig.savefig(fh, format='png')
        self.plt.close()
        fh.close()

    def getColor(self, k):
        return self.colors[k % len(self.colors)]
        
    def xBounds(self, *args, **kw):
        self.sp.xBounds(*args, **kw)
    
    def yBounds(self, *args, **kw):
        self.sp.yBounds(*args, **kw)

    def scaleTime(self, vectors):
        V0 = vectors[0]
        if not self.timex:
            return V0
        T_max = vectors[0].max()
        for mult, name in self.timeScales:
            if T_max < 1000*mult:
                break
        else:
            self.opts['xlabel'] = "seconds"
            return V0
        self.opts['xlabel'] = name
        self.opts['xscale'] = 1.0 / mult
        return V0 / mult 

    def parseArgs(self, args):
        vectors = []
        if not isinstance(args[0], (list, tuple, np.ndarray)):
            V = args[0]
            names = args[1:]
            for name in names:
                vectors.append(V[name])
            return vectors, names, V
        if self.V is not None:
            names = []
            for arg in args:
                if isinstance(arg, str) and arg in self.V:
                    names.append(arg)
                    vectors.append(self.V[arg])
                else:
                    names.append(None)
                    vectors.append(arg)
            if None in names:
                names = None
            return vectors, names, self.V
        return args, None, None

    def addLegend(thisVector, thisLegend):
        # Put an annotation at the right-most point where the
        # value is at least 99.9% of the vector maximum
        if max(thisVector) > 0:
            m999 = np.greater(thisVector, 0.999*max(thisVector))
        else:
            m999 = np.less(thisVector, 0.999*min(thisVector))
        k = max(np.nonzero(m999)[0])
        self.annotations.append((kVector, k, thisLegend))
    
    def __call__(self, *args, **kw):
        """
        Plots the second supplied vector (and any further ones) versus the
        first in the next subplot. If you supply an object that houses
        vectors and provides access to them as items, e.g.,
        C{analysis.sim.Vectors} of the I{pingspice} package, as the
        first argument, you can supply vector names instead of the
        vectors themselves.
        
        Options are set via the methods in L{OptsBase}, including a
        I{title}, a list of plot I{markers} and I{linestyles}, and a
        list of I{legend} entries for the plots with those
        keywords. I{legend} can also be set C{True} to use the default
        Matplotlib legend.

        Set I{useLabels} to C{True} to have annotation labels pointing
        to each plot line instead of a legend, with text taken from
        the legend list. (Works best in interactive apps.)

        Add other text annotations by the sample index of the point
        within the independent (first) and dependent vectors, the
        text, and the vector index. The vector index starts with 0 for
        the second vector argument and first dependent variable
        vector.

        Rescale all vectors after the first dependent one, relative to
        that first dependent one, by supplying a I{yscale}. This will
        result in two different twinned x-axes (one for the first
        dependent vector and one for everybody else) and a different
        y-axis label on the right.

        If you don't provide any such yScale, you can set I{bump} to
        C{True} to bump the common y-axis upper limit to 120% of what
        Matplotlib decides.

        Draw a dashed vertical line at a specified sample point by
        setting I{axvline} to an integer.

        If your x-axis is for time with units in seconds, you can set
        I{timex} to C{True} and the x values will be in set to the
        most sensible units, e.g., nanoseconds for values < 1E-6. Any
        'xlabel' keyword is disregarded in such case because the x
        label is set automatically.
        
        Any keywords you supply to this call are used to C{set\_X} the
        axes, e.g., C{ylabel="foo"} results in a C{set\_ylabel("foo")}
        command to the C{axes} object, for this subplot only.

        If you want to do everything with the next subplot on your own
        and only want a reference to its C{Axes} object, just call
        this with no args. You can still supply keywords to do
        C{set_X} stuff if you wish.
        """
        def getLast(obj, k):
            return obj[k] if k < len(obj) else obj[-1]

        def plotVector(k, vector, ax):
            if self.loglog: plotter = ax.loglog
            elif self.semilogx: plotter = ax.semilogx
            elif self.semilogy: plotter = ax.semilogy
            else: plotter = ax.plot 
            kw = {'scaley': not self.firstVectorTop}
            kw['marker'] = getLast(self.markers, k) \
                if self.markers else self.marker
            kw['linestyle'] = getLast(self.linestyles, k) \
                if self.linestyles else self.linestyle
            if kw['marker'] in (',', '.'): kw['linestyle'] = ''
            if kw['linestyle'] == '-': kw['linewidth'] = 2
            color = self.getColor(k)
            kw['color'] = color
            # Here is where the plotting actually happens
            lineInfo[0].extend(plotter(firstVector, vector, **kw))
            if yscale:
                ax.tick_params('y', colors=color)
                if k == 0:
                    ax.set_ylim(bottom=0)
                else: ax.set_ylim(0, axFirst.get_ylim()[1]/yscale)
            if isinstance(self.legend, bool):
                if self.legend and names:
                    legend = names[k+1]
                else:
                    return
            elif k < len(self.legend):
                legend = self.legend[k]
            else:
                return
            lineInfo[1].append(legend)
            if yscale: ax.set_ylabel(legend, color=color)
            if self.useLabels: self.addLegend(vector, legend)
        
        def adjustPlots(yscale, axvline):
            if self.bump and yscale is None:
                self.yBounds(ax, bump=True, zeroBottom=self.zeroBottom)
            elif self.firstVectorTop:
                self.yBounds(ax, Ymax=yMax, zeroBottom=self.zeroBottom)
            if isinstance(axvline, int) and abs(axvline) < len(firstVector):
                axFirst.axvline(
                    x=firstVector[axvline], linestyle='--', color="#404040")
            if self.legend and not self.annotations and not self.useLabels:
                axFirst.legend(*lineInfo, **{'loc': "best"})

        def doSettings(kw):
            for name in self.kw:
                kw.setdefault(name, self.kw[name])
            for name in self._settings:
                if self.opts[name]:
                    kw.setdefault(name, self.opts[name])
            for name in kw:
                self.sp.set_(name, kw[name])

        def doAnnotations(yscale):
            self.plt.draw()
            annotator = self.annotators[axFirst] = Annotator(
                axList, [firstVector]+list(vectors[1:]))
            for k, text, kVector in self.annotations:
                x = firstVector[k]
                y = vectors[kVector+1][k]
                kAxis = 0 if yscale is None or kVector == 0 else 1
                annotator(kAxis, x, y, text)
            annotator.update()

        ax = axFirst = self.sp[None]
        if not args:
            doSettings(kw)
            return ax
        lineInfo = [[],[]]
        yscale = self.yscale
        vectors, names, V = self.parseArgs(args)
        firstVector = self.scaleTime(vectors)
        N = len(firstVector)
        yMax = -np.inf
        for kVector, thisVector in enumerate(vectors[1:]):
            thisMax = thisVector.max()
            if thisMax > yMax:
                yMax = thisMax
            if yscale and kVector == 1:
                ax = self.sp.twinx()
            plotVector(kVector, thisVector, ax)
        adjustPlots(yscale, self.axvline)
        doSettings(kw)
        axList = self.sp.getTwins()
        if self.annotations:
            doAnnotations(yscale)
        axList = [SpecialAx(ax, self.opts, V) for ax in axList]
        if len(axList) == 1:
            return axList[0]
        return axList
