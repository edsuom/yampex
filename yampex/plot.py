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
from copy import deepcopy
import importlib

import screeninfo

import numpy as np

from yampex.options import OptsBase
from yampex.annotate import Annotator, TextBoxMaker
from yampex.subplot import Subplotter
from yampex.scaling import Scaler
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


class SpecialAx(object):
    """
    I pretend to be a C{matplotlib.Axes} object except that I
    intercept plotting calls and rescale the independent vector first.

    Construct me with a subplot axes object I{ax}, a dict of options
    I{opts} for the subplot, and a vector container object I{V}.

    If your call to a L{Plotter} instance (most likely in a subplot
    context) has a container object as its first argument, I will
    replace the arguments with actual Numpy vectors element-wise
    accessed from that cotnainer object. The underlying Matplotlib
    call will only see the Numpy vectors. For example,::

        import numpy as np
        V = {'x': np.linspace(0, 1, 100)}
        V['y'] = V['x']**2
        with Plotter(1) as sp:
            sp(V, 'x', 'y')

    will plot the square of I{x} vs I{x}. This comes in handy when you
    have containers full of vectors and you want to plot selected ones
    of them in different subplots.
    
    The container object I{V} will be C{None} if vector objects rather
    than names were supplied to my plotting call.
    """
    _plotterNames = {
        'plot', 'loglog',
        'semilogx', 'semilogy', 'scatter', 'step', 'bar', 'stem'}
    
    def __init__(self, ax, opts, V):
        """C{SpecialAx(ax, opts, V)}"""
        self.ax = ax
        self.opts = opts
        self.V = V

    def __getattr__(self, name):
        """
        Returns a plotting method wrapped in a wrapper function that first
        looks up vector names from my vector container I{V} (if it's
        not a C{None} object) and does x-axis scaling.
        """
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

    Use the "Agg" backend by supplying the keyword I{useAgg} or
    calling the L{useAgg} class method. This works better for plotting
    to an image file, and is selected automatically if you supply a
    I{filePath} to the constructor. Be aware that, once selected, that
    backend will be used for all instances of me. If you're using the
    "Agg" backend, you should specify it the first time an instance is
    constructed, or beforehand with the L{useAgg} class method.
    
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
    colors = ['b', 'g', 'r', '#40C0C0', '#C0C040', '#C040C0', '#8080FF']
    timeScales = [
        (1E-9,          "Nanoseconds"),
        (1E-6,          "Microseconds"),
        (1E-3,          "Milliseconds"),
        (1.0,           "Seconds"),
        (60.0,          "Minutes"),
        (3600.0,        "Hours"),
    ]

    _opts = {
        'settings':             {},
        'plotKeywords':         {},
        'marker':               ('', None),
        'markers':              [],
        'linestyles':           [],
        'grid':                 False,
        'firstVectorTop':       False,
        'loglog':               False,
        'semilogx':             False,
        'semilogy':             False,
        'bar':                  False,
        'stem':                 False,
        'step':                 False,
        'error':                False,
        'legend':               [],
        'annotations':          [],
        'textBoxes':            {},
        'xscale':               None,
        'yscale':               None,
        'axisExact':            {},
        'ticks':                {},
        'useLabels':            False,
        'axvlines':             [],
        'bump':                 False,
        'timex':                False,
        'xlabel':               "",
        'ylabel':               "",
        'title':                "",
        'zeroBottom':           False,
        'zeroLine':             False,
        'fontsizes':            {},
    }
    _settings = {'title', 'xlabel', 'ylabel'}
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
            Nc = N
            Nr = args.pop(0)
        else:
            Nc = self.N_cols(N)
            Nr = int(np.ceil(float(N)/Nc))
        self.V = args[0] if args else None
        self.opts = deepcopy(self._opts)
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
        self.sp = Subplotter(self, Nc, Nr)
        self.dims = {}
        self.annotators = {}
        self.kw = kw
        self._figTitle = None
        self._isSubplot = False
        self._xlabels = {}
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
        Upon context entry, sets up the next (first) subplot with cleared
        axes, preserves a copy of my global (all subplots) options,
        and returns a reference to myself.
        """
        self.sp.setup()
        self._isSubplot = True
        self.global_opts = self.opts
        self.opts = deepcopy(self.global_opts)            
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

    def textDims(self, textObj):
        """
        Returns the dimensions of the supplied text object in pixels.

        If there's no renderer yet, estimates the dimensions based on
        font size and DPI.
        """
        try:
            bb = textObj.get_window_extent()
            dims = bb.width, bb.height
        except:
            size = self.DPI * textObj.get_size() / 72
            dims = [0.4*size*len(textObj.get_text()), size]
        return dims
    
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
        self.opts = deepcopy(self.global_opts)            

    def subplots_adjust(self):
        """
        Calls C{subplots_adjust} on my figure, doing a bit of tweaking
        first.
        """
        def width(x=None):
            if x is None:
                return self.fig.get_window_extent().width
            return self.textDims(x)[0]

        def height(x=None):
            if x is None:
                return self.fig.get_window_extent().height
            return self.textDims(x)[1] * 1.5

        def tickWidth(k):
            maxTickWidth = 0
            for ytl in self.sp[k].get_yticklabels():
                thisWidth = width(ytl)
                if thisWidth > maxTickWidth:
                    maxTickWidth = thisWidth
            return maxTickWidth
        
        def tickHeight(k):
            maxTickHeight = 0
            for ytl in self.sp[k].get_yticklabels():
                thisHeight = height(ytl)
                if thisHeight > maxTickHeight:
                    maxTickHeight = thisHeight
            return maxTickHeight
        
        def wSpace(left=False):
            maxWidth = 0
            for k in range(len(self.sp)):
                if left and not self.sp.onLeft(k):
                    continue
                thisWidth = tickWidth(k)
                dims = self.dims[k].get('ylabel', None)
                if dims:
                    # Add twice the ylabel's font height (not width,
                    # because rotated 90)
                    thisWidth += 2*dims[1]
                if thisWidth > maxWidth:
                    maxWidth = thisWidth
            return maxWidth

        def hSpace(top=False, bottom=False):
            maxHeight = 0
            for k in range(len(self.sp)):
                if top and not self.sp.onTop(k):
                    continue
                if bottom and not self.sp.atBottom(k):
                    continue
                thisHeight = 0
                if not top:
                    # Ticks
                    thisHeight += tickHeight(k)
                    # Subplot xlabel, if shown for this row
                    if not universal_xlabel or self.sp.atBottom():
                        dims = self.dims[k].get('xlabel', None)
                        if dims:
                            # Add twice the xlabel's font height
                            thisHeight += 2*dims[1]
                # Subplot title
                if not bottom:
                    dims = self.dims[k].get('title', None)
                    if dims:
                        # Add twice the title's font height
                        thisHeight += 2*dims[1]
                if thisHeight > maxHeight:
                    maxHeight = thisHeight
            return maxHeight

        def scaledWidth(x, per_sp=False, scale=1.0, margin=30):
            pw = width()
            if per_sp: pw /= self.sp.Nc
            return scale*(x+margin) / pw

        def scaledHeight(x, per_sp=False, scale=1.0, margin=30):
            ph = height()
            if per_sp: ph /= self.sp.Nr
            return scale*(x+margin) / ph
        
        kw = {}
        fWidth = width(); fHeight = height()
        if self._figTitle:
            titleHeight = height(self.fig.suptitle(self._figTitle))
        else: titleHeight = 0
        universal_xlabel = self._universal_xlabel
        if universal_xlabel:
            # Thanks to kennytm,
            # https://stackoverflow.com/questions/3844801/
            #  check-if-all-elements-in-a-list-are-identical
            if len(set(self._xlabels.values())) > 1:
                universal_xlabel = False
        textObj = None
        for k in self._xlabels:
            if universal_xlabel and not self.sp.atBottom(k):
                continue
            ax = self.sp.axes[k]
            ax.set_xlabel(self._xlabels[k])
        kw['top'] = 1.0 - scaledHeight(hSpace(top=True)+titleHeight)
        kw['hspace'] = scaledHeight(hSpace(), per_sp=True)
        kw['bottom'] = scaledHeight(hSpace(bottom=True), margin=15)
        kw['wspace'] = scaledWidth(wSpace(), per_sp=True)
        kw['left'] = scaledWidth(wSpace(left=True))
        try:
            self.fig.subplots_adjust(**kw)
        except ValueError as e:
            if self.verbose:
                print(sub(
                    "WARNING: ValueError '{}' doing subplots_adjust({})",
                    e.message,
                    ", ".join([sub("{}={}", x, kw[x]) for x in kw])))
    
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
            
    def getColor(self, k):
        """
        Supply an integer index starting from zero and this returns a
        color from a clean and simple default palette.
        """
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
            if mult < 1:
                if T_max < 1000*mult:
                    break
            elif T_max < 150*mult:
                break
        self.opts['xlabel'] = name
        self.opts['xscale'] = 1.0 / mult
        return V0 / mult 

    def pickPlotter(self, ax, plotter, kw):
        bogusMap = {
            'bar': ('marker', 'linestyle', 'scaley'),
            'step': ('marker', 'linestyle', 'scaley'),
        }
        for name in (
                'loglog', 'semilogx', 'semilogy',
                'bar', 'step', 'stem', 'error'):
            if plotter == name or getattr(self, name, False):
                for bogus in bogusMap.get(name, []):
                    kw.pop(bogus, None)
                return getattr(ax, name)
        return ax.plot 
    
    def parseArgs(self, args):
        def arrayify(x):
            if isinstance(x, np.ndarray):
                return x
            return np.array(x)
        
        vectors = []
        if not isinstance(args[0], (list, tuple, np.ndarray)):
            V = args[0]
            names = args[1:]
            for name in names:
                vectors.append(arrayify(V[name]))
            return vectors, names, V
        if self.V is not None:
            names = []
            for arg in args:
                if isinstance(arg, str) and arg in self.V:
                    names.append(arg)
                    vectors.append(arrayify(self.V[arg]))
                else:
                    names.append(None)
                    vectors.append(arrayify(arg))
            if None in names:
                names = None
            return vectors, names, self.V
        return [arrayify(x) for x in args], None, None

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
        def getLast(obj, k):
            return obj[k] if k < len(obj) else obj[-1]

        def plotVector(k, vector, ax, kw_orig):
            kw = {}
            kw['scaley'] = not self.firstVectorTop
            kw['marker'], size = getLast(self.markers, k) \
                if self.markers else self.marker
            if size is not None:
                kw['markersize'] = size
            width = 2
            if self.linestyles:
                kw['linestyle'], width = getLast(self.linestyles, k)
            elif kw['marker'] in (',', '.'):
                kw['linestyle'] = ''
            else: kw['linestyle'] = '-'
            kw['linewidth'] = width
            color = self.getColor(k)
            kw['color'] = color
            # Original keywords override any already set
            kw.update(kw_orig)
            # Here is where the plotting actually happens
            plotter = self.pickPlotter(ax, kw_plotter, kw)
            lineInfo[0].extend(plotter(firstVector, vector, **kw))
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
                ax.set_xlim(firstVector.min(), firstVector.max())
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
                    if abs(axvline) < len(firstVector):
                        x = firstVector[axvline]
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

        def doSettings():
            def bbAdd(textObj):
                dims = self.textDims(textObj)
                self.dims.setdefault(k, {})[name] = dims

            k = self.sp.kLast
            for name in self._settings:
                value = self.opts[name]
                if not value: continue
                bbAdd(self.sp.set_(name, value))
                if name == 'xlabel':
                    self._xlabels[k] = value
                    continue
            for name in self.settings:
                bbAdd(self.sp.set_(name, self.settings[name]))
        
        def doAnnotations(yscale):
            self.plt.draw()
            annotator = self.annotators[axFirst] = Annotator(
                axList, [firstVector]+list(vectors[1:]),
                fontsize=self.fontsizes.get('annotations', 'small'))
            for k, text, kVector, is_yValue in self.annotations:
                Y = vectors[kVector+1]
                if not isinstance(k, int):
                    if is_yValue:
                        k = np.argmin(np.abs(Y-k))
                    else: k = np.searchsorted(firstVector, k)
                x = firstVector[k]
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
        if not args:
            axList = [ax]
            doSettings()
        else:
            lineInfo = [[], []]
            yscale = self.yscale
            vectors, names, V = self.parseArgs(args)
            if len(vectors) == 1:
                # Just one vector supplied, create x-axis range vector
                # for it
                vectors.insert(0, np.arange(len(vectors[0])))
            firstVector = self.scaleTime(vectors)
            doSettings()
            if yscale is True:
                if len(vectors) > 2:
                    scaler = Scaler(vectors[1])
                    yscales = [scaler(x) for x in vectors[2:]]
                    yscale = 1 if 1 in yscales else min(yscales)
                else: yscale = 1
            N = len(firstVector)
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
                doAnnotations(yscale)
            if self.textBoxes:
                tbm = TextBoxMaker(axFirst, self.sp.Nc, self.sp.Nr)
                for quadrant in self.textBoxes:
                    tbm(quadrant, self.textBoxes[quadrant])
            axList = [SpecialAx(ax, self.opts, V) for ax in axList]
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
        
