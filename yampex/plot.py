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
You'll do everything with a L{Plotter} in context.

Keep the API for its L{OptsBase} base class handy, and maybe a copy of
its U{source<http://edsuom.com/yampex/yampex.options.py>}, to see all
the plotting options you can set.
"""

import weakref
import importlib

import screeninfo

import numpy as np

from yampex.options import Opts, OptsBase
from yampex.annotate import Annotator, TextBoxMaker
from yampex.subplot import Subplotter
from yampex.scaling import Scaler
from yampex.adjust import Adjuster
from yampex.util import sub


class PlotterHolder(object):
    """
    L{Plotter} uses a class-wide instance of me to hold weak
    references to its instances.

    @see: L{Plotter.showAll}, which uses my weak references to show
        the Matplotlib figures for all instances of L{Plotter} and
        then remove them.
    """
    def __init__(self):
        """C{PlotterHolder()}"""
        self.pDict = weakref.WeakValueDictionary()

    def add(self, obj):
        """
        Adds the L{Plotter} instance (or anything, really, but plotters
        are what I was intended for) to my weak-reference registry.

        Returns an integer ID that you can use with a call to
        L{remove} and thus avoid having to keep a reference to the
        object yourself.
        """
        ID = id(obj)
        self.pDict[ID] = obj
        return ID

    def remove(self, ID):
        """
        Removes the L{Plotter} instance identified by the supplied I{ID}
        from my weak-reference registry.
        """
        if ID in self.pDict:
            del self.pDict[ID]

    def removeAll(self):
        """
        Removes all L{Plotter} instances from my weak-reference registry.
        """
        self.pDict.clear()
            
    def doForAll(self, methodName, *args, **kw):
        """
        Does the method named I{methodName}, with any args and kw, for
        each L{Plotter} instance I'm keeping track of.
        
        Returns C{True} if there was at least one object that successfully
        performed I{methodName}.
        """
        OK = False
        for ID in self.pDict.keys():
            if ID in self.pDict:
                OK = True
                try:
                    getattr(self.pDict[ID], methodName)(*args, **kw)
                except: OK = False
        return OK

    
class Plotter(OptsBase):
    """
    I provide a Matplotlib C{Figure} with one or more time-vector and
    XY subplots of Numpy vectors.

    Construct an instance of me with the total number of subplots (to
    be intelligently apportioned into one or more rows and columns)
    or, with two constructor arguments, the number of columns followed
    by the number of rows.

    With the I{filePath} keyword, you can specify the file path of a
    PNG file for me to create or overwrite with each call to L{show}.
    
    You can set the I{width} and I{height} of the Figure in inches
    (calculated with 100 DPI) with constructor keywords, and
    (read-only) access them via my properties of the same names. Or
    set my I{figSize} attribute (in a subclass or with that
    constructor keyword) to a 2-sequence with figure width and height
    in inches. The default width and height is just shy of the entire
    monitor size.

    Use the "Agg" backend by supplying the constructor keyword
    I{useAgg}. This works better for plotting to an image file, and is
    selected automatically if you supply a I{filePath} to the
    constructor. Be aware that, once selected, that backend will be
    used for all instances of me. If you're using the "Agg" backend,
    you should specify it the first time an instance is constructed.

    Setting the I{verbose} keyword C{True} puts out a bit of info
    about annotator positioning. Not for regular use.
    
    Any other keywords you supply to the constructor are supplied to
    the underlying Matplotlib plotting call for all
    subplots.

    Keep the API for L{OptsBase} handy, and maybe a copy of the
    U{source<http://edsuom.com/yampex/yampex.plot.py>}, to see all the
    plotting options you can set.

    @ivar dims: A dict of sub-dicts of the dimensions of various text
        objects, keyed first by subplot index then the object name.
    """
    ph = PlotterHolder()
    
    fc = None
    DPI = 100 # Don't change this, for reference only
    figSize = None
    timeScales = [
        (1E-9,          "Nanoseconds"),
        (1E-6,          "Microseconds"),
        (1E-3,          "Milliseconds"),
        (1.0,           "Seconds"),
        (60.0,          "Minutes"),
        (3600.0,        "Hours"),
    ]
    # Show warnings?
    verbose = False

    @classmethod
    def setup(cls, useAgg=False):
        """
        Called by each instance of me during instantiation. Sets a
        class-wide Matplotlib pyplot import the first time it's
        called.
        """
        if useAgg and not getattr(cls, '_usingAgg', False):
            mpl = importlib.import_module("matplotlib")
            mpl.use('Agg')
            cls._usingAgg = True
        if not getattr(cls, 'plt', None):
            cls.plt = importlib.import_module("matplotlib.pyplot")

    @classmethod
    def showAll(cls):
        """
        Calls L{show} for the figures generated by all instances of me.
        """
        OK = cls.ph.doForAll('show', noShow=True)
        if OK: cls.plt.show()
        cls.ph.doForAll('clear')
        # They should all have removed themselves now, but what the
        # heck, clear it anyways
        cls.ph.removeAll()
            
    def __init__(self, N, *args, **kw):
        """C{Plotter(N, *args, **kw)}"""
        args = list(args)
        if args:
            # Nc, Nr specified
            Nc = N
            Nr = args.pop(0)
            N = Nc*Nr
        else:
            # N specified
            Nc = self.N_cols(N)
            Nr = int(np.ceil(float(N)/Nc))
        self.V = args[0] if args else None
        self.opts = Opts()
        self.filePath = kw.pop('filePath', None)
        if 'verbose' in kw: self.verbose = kw.pop('verbose')
        useAgg = bool(self.filePath) or kw.pop('useAgg', False)
        self.setup(useAgg=useAgg)
        figSize = kw.pop('figSize', self.figSize)
        if figSize is None:
            if useAgg:
                figSize = [10.0, 7.0]
            else:
                si = screeninfo.screeninfo.get_monitors()[0]
                figSize = [float(x)/self.DPI for x in (si.width-80, si.height-80)]
        if 'width' in kw:
            figSize[0] = kw.pop('width')
        if 'height' in kw:
            figSize[1] = kw.pop('height')
        self.figSize = figSize
        self.fig = self.plt.figure(figsize=figSize)
        if not useAgg:
            self.fig.canvas.mpl_connect(
                'resize_event', self.subplots_adjust)
        self.dims = {}
        self.sp = Subplotter(self, N, Nc, Nr)
        self.adj = Adjuster(self)
        self.annotators = {}
        self.kw = kw
        self._figTitle = None
        self._isSubplot = False
        self.xlabels = {}
        self._universal_xlabel = False
        if self.verbose:
            Annotator.setVerbose(True)
        # This is an integer, not a reference to anything
        self.ID = self.ph.add(self)

    def __del__(self):
        """
        Safely ensures that I am removed from the class-wide I{ph}
        instance of L{PlotterHolder}.
        """
        # Only an integer is passed to the call
        self.ph.remove(self.ID)
        # No new references were created, nothing retained

    def subplots_adjust(self, *args):
        dimThing = args[0] if args else self.fig.get_window_extent()
        fWidth, fHeight = [getattr(dimThing, x) for x in ('width', 'height')]
        self.adj.updateFigSize(fWidth, fHeight)
        # This causes trouble because Matplotlib increases spacing
        # above the title as the figure gets bigger, and it's
        # difficult to figure out how much extra space to add.
        if self._figTitle:
            fontsize = self.opts['fontsizes'].get('title', None)
            kw = {'fontsize':fontsize} if fontsize else {}
            titleObj = self.fig.suptitle(self._figTitle, **kw)
            titleHeight = self.adj.height(titleObj)
            # Scale the title height a bit with figure size to make up for
            # the extra space above
            titleHeight *= 1 + max([0, (fHeight-400)/500])
        else: titleHeight = 0
        kw = self.adj(self.xlabels, self._universal_xlabel, titleHeight)
        try:
            self.fig.subplots_adjust(**kw)
        except ValueError as e:
            if self.verbose:
                print(sub(
                    "WARNING: ValueError '{}' doing subplots_adjust({})",
                    e.message,
                    ", ".join([sub("{}={}", x, kw[x]) for x in kw])))
        
    @property
    def width(self):
        """
        Figure width (inches).
        """
        return self.fig.get_figwidth()

    @property
    def height(self):
        """
        Figure height (inches).
        """
        return self.fig.get_figheight()
        
    def __nonzero__(self):
        """
        I evaluate as C{True} if I have any subplots defined yet.
        """
        return bool(len(self.sp))
        
    def __getattr__(self, name):
        """
        You can access a given subplot's plotting options as an attribute.
        """
        if name in self.opts:
            return self.opts[name]
        raise AttributeError(sub(
            "No plotting option or attribute '{}'", name))
        
    def __enter__(self):
        """
        Upon an outer context entry, sets up the first subplot with cleared
        axes, preserves a copy of my global (all subplots) options,
        and returns a reference to myself.
        """
        self.sp.setup()
        self._isSubplot = True
        self.global_opts = self.opts
        self.opts = self.global_opts.deepcopy()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Upon completion of context, turns minor ticks and grid on if
        enabled for this subplot's axis, and restores global (all
        subplots) options.
        """
        self._isSubplot = False
        self.opts = self.global_opts
        del self.global_opts

    def N_cols(self, N):
        """
        Returns the number of columns, given the total number of
        subplots. There will be either one, two, or three columns.
        """
        if N > 6:
            return 3
        if N > 3:
            return 2
        return 1
    
    def post_op(self):
        """
        Call this once after each subplot: Adds minor ticks and a grid,
        depending on the subplot-specific options. Then sets my
        I{opts} dict to a copy of the global (all subplots) options.
        """
        ax = self.sp.ax
        if ax is None: return
        self.sp.setTicks(self.ticks)
        if self.grid:
            ax.grid(True, which='major')
        self.opts = self.global_opts.deepcopy()
    
    def show(self, windowTitle=None, fh=None, filePath=None, noShow=False):
        """
        Call this to show the figure with suplots after the last call to
        my instance.
        
        If I have a non-C{None} I{fc} attribute (which must reference
        an instance of Qt's C{FigureCanvas}, then the FigureCanvas is
        drawn instead of PyPlot doing a window show.

        You can supply an open file-like object for PNG data to be
        written to (instead of a Matplotlib Figure being displayed)
        with the I{fh} keyword. (It's up to you to close the file
        object.)

        Or, with the I{filePath} keyword, you can specify the file
        path of a PNG file for me to create or overwrite. (That
        overrides any I{filePath} you set in the constructor.)
        """
        try:
            self.fig.tight_layout()
        except ValueError as e:
            if self.verbose:
                proto = "WARNING: ValueError '{}' doing tight_layout "+\
                        "on {:.5g} x {:.5g} figure"
                print(sub(proto, e.message, self.width, self.height))
        self.subplots_adjust()
        # Calling plt.draw massively slows things down when generating
        # plot images on Rpi. And without it, the (un-annotated) plot
        # still updates!
        if self.annotators:
            self.plt.draw()
            for annotator in self.annotators.values():
                annotator.update()
        if fh is None:
            if filePath is None: filePath = self.filePath
            if filePath:
                fh = open(filePath, 'wb+')
        if fh is None:
            self.plt.draw()
            if windowTitle:
                self.fig.canvas.set_window_title(windowTitle)
            if self.fc is not None:
                self.fc.draw()
            elif not noShow:
                self.plt.show()
        else:
            self.fig.savefig(fh, format='png')
            self.plt.close()
            if filePath is not None:
                # Only close a file handle I opened myself
                fh.close()
        if not noShow:
            self.clear()

    def clear(self):
        self.fig.clear()
        self.annotators.clear()
        self.dims.clear()
        self.ph.remove(self.ID)
            
    def xBounds(self, *args, **kw):
        self.sp.xBounds(*args, **kw)
    
    def yBounds(self, *args, **kw):
        self.sp.yBounds(*args, **kw)

    def scaleTime(self, X):
        if not self.timex:
            return
        T_max = X.max()
        for mult, name in self.timeScales:
            if mult < 1:
                if T_max < 1000*mult:
                    break
            elif T_max < 150*mult:
                break
        self.opts['xlabel'] = name
        self.opts['xscale'] = 1.0 / mult

    def pickPlotter(self, ax, plotter, kw):
        bogusMap = {
            'bar': ('marker', 'linestyle', 'scaley'),
            'step': ('marker', 'linestyle', 'scaley'),
        }
        kw['_no_parse'] = True
        for name in (
                'loglog', 'semilogx', 'semilogy',
                'bar', 'step', 'stem', 'error'):
            if plotter == name or getattr(self, name, False):
                for bogus in bogusMap.get(name, []):
                    kw.pop(bogus, None)
                return getattr(ax, name)
        return ax.plot 

    def addLegend(self, thisVector, thisLegend):
        # Put an annotation at the right-most point where the
        # value is at least 99.9% of the vector maximum
        if max(thisVector) > 0:
            m999 = np.greater(thisVector, 0.999*max(thisVector))
        else:
            m999 = np.less(thisVector, 0.999*min(thisVector))
        k = max(np.nonzero(m999)[0])
        self.annotations.append((kVector, k, thisLegend, False))

    def __call__(self, *args, **kw):
        """
        In the next subplot, plots the second supplied vector (and any
        further ones) versus the first.

        If you supply a container object that houses vectors and
        provides access to them as items as the first argument, you
        can supply vector names instead of the vectors themselves. The
        container object must evaluate C{NAME in OBJ} as C{True} if it
        contains a vector with NAME, and must return the vector with
        C{OBJ[NAME]}.
        
        Options are set via the methods in L{OptsBase}, including a
        I{title}, a list of plot I{markers} and I{linestyles}, and a
        list of I{legend} entries for the plots with those
        keywords. I{legend} can also be set C{True} to use the default
        Matplotlib legend.

        Set I{useLabels} to C{True} to have annotation labels pointing
        to each plot line instead of a legend, with text taken from
        the legend list. (Works best in interactive apps.)

        Rescale all vectors after the first dependent one, relative to
        that first dependent one, by setting a y scale with a call to
        L{OptsBase.set_yscale} before making this plotting call. That
        will result in two different twinned x-axes (one for the first
        dependent vector and one for everybody else) and a different
        y-axis label on the right. Use a scale < 1 if the second (and
        later) vectors are bigger than the first and you want them to
        look smaller.

        If you don't provide any such yScale, you can set I{bump} to
        C{True} to bump the common y-axis upper limit to 120% of what
        Matplotlib decides.

        If your x-axis is for time with units in seconds, you can set
        I{timex} to C{True} and the x values will be in set to the
        most sensible units, e.g., nanoseconds for values < 1E-6. Any
        'xlabel' keyword is disregarded in such case because the x
        label is set automatically.

        You can override my default plotter by specifying the name of
        another one with the I{plotter} keyword, e.g.,
        C{plotter="step"}.
        
        Any other keywords you supply to this call are supplied to the
        underlying Matplotlib plotting call. (B{NOTE:} This is a
        change from previous versions of Yampex where keywords to this
        method were used to C{set_X} the axes, e.g., C{ylabel="foo"}
        results in a C{set_ylabel("foo")} command to the C{axes}
        object, for this subplot only. Use the new L{OptsBase.set}
        command instead.)

        Returns a list of the axes created for the plot, or an C{Axes}
        object if just one was created.
        
        If you want to do everything with the next subplot on your own
        and only want a reference to its C{Axes} object, just call
        this with no args. In this case, however, you will need to
        call L{post_op} yourself after you're done doing what this
        call would ordinarily do.
        """
        def plotVector(k, vector, ax, kw):
            # Here is where the plotting actually happens
            kw = self.opts.kwModified(k, kw)
            plotter = self.pickPlotter(ax, kw_plotter, kw)
            lineInfo[0].extend(plotter(X, vector, **kw))
            if yscale:
                ax.tick_params('y', colors=color)
                if k == 0:
                    ax.set_ylim(bottom=0)
                else: ax.set_ylim(0, axFirst.get_ylim()[1]*yscale)
            if isinstance(self.legend, bool):
                if self.legend and names:
                    legend = names[k+1]
                else: return
            elif k < len(self.legend):
                legend = self.legend[k]
            else: return
            lineInfo[1].append(legend)
            if yscale: ax.set_ylabel(legend, color=color)
            if self.useLabels: self.addLegend(vector, legend)
        
        def adjustPlots(yscale, axvlines):
            if self.axisExact.get('x', False):
                ax.set_xlim(X.min(), X.max())
            if self.axisExact.get('y', False):
                V = np.array(vectors[1:])
                ax.set_ylim(V.min(), V.max())
            elif self.bump and yscale is None:
                self.yBounds(ax, bump=True, zeroBottom=self.zeroBottom)
            elif self.firstVectorTop and yMax is not None:
                self.yBounds(ax, Ymax=yMax, zeroBottom=self.zeroBottom)
            for axvline in axvlines:
                x = None
                if isinstance(axvline, int):
                    if abs(axvline) < len(X):
                        x = X[axvline]
                else: x = axvline
                if x is None: continue
                axFirst.axvline(x=x, linestyle='--', color="#404040")
            # Zero line (which may be non-zero)
            yz = self.zeroLine
            if yz is True: yz = 0
            if yz is not None and yz is not False:
                y0, y1 = axFirst.get_ylim()
                if y0 < yz and y1 > yz:
                    axFirst.axhline(
                        y=yz, linestyle='--',
                        linewidth=1, color="black", zorder=10)
            if self.legend and (not self.annotations or not self.useLabels):
                axFirst.legend(*lineInfo, **{
                    'loc': "best",
                    'fontsize': self.fontsizes.get('legend', "small")})

        def doAnnotations(axList, yscale):
            self.plt.draw()
            annotator = self.annotators[axList[0]] = Annotator(
                axList, [X]+list(vectors[1:]),
                fontsize=self.fontsizes.get('annotations', 'small'))
            for k, text, kVector, is_yValue in self.annotations:
                Y = vectors[kVector+1]
                if not isinstance(k, int):
                    if is_yValue:
                        k = np.argmin(np.abs(Y-k))
                    else: k = np.searchsorted(X, k)
                x = X[k]
                y = Y[k]
                kAxis = 0 if yscale is None or kVector == 0 else 1
                if isinstance(text, int):
                    text = sub("{:d}", text)
                elif isinstance(text, float):
                    text = sub("{:.2f}", text)
                annotator(kAxis, x, y, text)
                annotator.update()

        ax = axFirst = self.sp[kw.pop('k', None)]
        # Apply plot keywords set via the set_plotKeyword call and
        # then, with higher priority, those set via the constructor,
        # if they don't conflict with explicitly set keywords to this
        # call which takes highest priority
        for thisDict in (self.kw, self.plotKeywords):
            for name in thisDict:
                if name not in kw:
                    kw[name] = thisDict[name]
        # The 'plotter' keyword is reserved for Yampex, unrecognized
        # by Matplotlib
        kw_plotter = kw.pop('plotter', None)
        if 'scaley' not in kw:
            kw['scaley'] = not self.firstVectorTop
        if not args:
            axList = [ax]
            ax.helper.doSettings()
        else:
            lineInfo = [[], []]
            yscale = self.yscale
            ax.helper.parseArgs(args)
            # TODO: Be smarter than this
            vectors, names = ax.helper.vectors, ax.helper.names
            X = vectors[0]
            self.scaleTime(X)
            ax.helper.doSettings()
            if yscale is True:
                if len(vectors) > 2:
                    scaler = Scaler(vectors[1])
                    yscales = [scaler(x) for x in vectors[2:]]
                    yscale = 1 if 1 in yscales else min(yscales)
                else: yscale = 1
            N = len(X)
            yMax = None
            for kVector, thisVector in enumerate(vectors[1:]):
                if len(thisVector):
                    thisMax = thisVector.max()
                    if yMax is None or thisMax > yMax:
                        yMax = thisMax
                if yscale and kVector == 1:
                    ax = self.sp.twinx()
                plotVector(kVector, thisVector, ax, kw)
            adjustPlots(yscale, self.axvlines)
            axList = self.sp.getTwins()
            if self.annotations:
                doAnnotations(axList, yscale)
            if self.textBoxes:
                tbm = TextBoxMaker(axFirst, self.sp.Nc, self.sp.Nr)
                for quadrant in self.textBoxes:
                    tbm(quadrant, self.textBoxes[quadrant])
            self.post_op()
        if len(axList) == 1:
            return axList[0]
        return axList

    def get_annotators(self, ax=None):
        """
        Returns the annotator for the supplied axes object, or a list of
        all annotators if no axes object is supplied.
        """
        if ax is None:
            return self.annotators.values()
        if ax not in self.annotators:
            axax = getattr(ax, 'ax', None)
            if axax and axax in self.annotators:
                ax = axax
            else:
                print(sub("No annotator for axes object '{}'", repr(ax)))
                import pdb; pdb.set_trace()
        return self.annotators[ax]
        
