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
You'll do everything with a L{Plotter} in context.

Keep the API for its L{OptsBase} base class handy, and maybe a copy of
its U{source<http://edsuom.com/yampex/yampex.options.py>}, to see all
the plotting options you can set.
"""

import weakref
import importlib

try:
    import screeninfo
except: screeninfo = None

import numpy as np

from yampex.textbox import TextBoxMaker
from yampex.options import Opts, OptsBase
from yampex.subplot import Subplotter
from yampex.scaling import Scaler
from yampex.adjust import Adjuster
from yampex.util import PLOTTER_NAMES, sub


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
        for ID in list(self.pDict.keys()):
            if ID in self.pDict:
                OK = True
                try:
                    getattr(self.pDict[ID], methodName)(*args, **kw)
                except: OK = False
        return OK


class Dims(object):
    """
    I store dimensions of things for each subplot. If my I{debug}
    class attribute is set C{True}, I print info about what's being
    set and get for debugging purposes.
    """
    debug = False

    def __init__(self):
        self.sp_dicts = {}

    def clear(self):
        """
        Clears out all my info.
        """
        if self.debug:
            print("DIMS cleared")
        self.sp_dicts.clear()

    def setDims(self, k, name, dims):
        """
        For subplot I{k} (index starts at zero), sets the X and Y
        dimensions of an object with the specified I{name} to the
        supplied sequence I{dims}.
        """
        dims = tuple(dims)
        if self.debug:
            print(sub("DIMS {:d}: {} <-- {}", k, name, dims))
        self.sp_dicts.setdefault(k, {})[name] = dims

    def getDims(self, k, name):
        """
        For subplot I{k}, returns the dimension of the object with the
        specified I{name} or C{None} if no such dimension has been
        set.
        """
        if k not in self.sp_dicts: return
        value = self.sp_dicts[k].get(name, None)
        if self.debug:
            print(sub("DIMS {:d}: {} -> {}", k, name, value))
        return value
        
    
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
    
    You can set the I{width} and I{height} of the Figure with
    constructor keywords, and (read-only) access them via my
    properties of the same names. Or set my I{figSize} attribute (in a
    subclass or with that constructor keyword) to a 2-sequence with
    figure width and height. The default width and height is just shy
    of the entire monitor size.

    The dimensions are in inches, converted to pixels at 100 DPI,
    unless they are both integers and either of them exceeds 75 (which
    would equate to a huge 7,500 pixels). In that case, they are
    considered to specify the pixel dimensions directly.

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

    @ivar dims: A dict (actually, a subclass of L{Dims}) of sub-dicts
        of the dimensions of various text objects, keyed first by
        subplot index then the object name.

    @ivar Nsp: The number of subplots defined thus far defined with
        calls to my instance.
    """
    ph = PlotterHolder()
    
    fc = None
    DPI = 100 # Don't change this, for reference only
    _settings = {'title', 'xlabel', 'ylabel'}
    figSize = None
    # Flag to indicate if using Agg rendererer (for generating PNG files)
    usingAgg = False
    # Show warnings? (Not for regular use.)
    verbose = False

    @classmethod
    def setupClass(cls, useAgg=False):
        """
        Called by each instance of me during instantiation. Sets a
        class-wide Matplotlib pyplot import the first time it's
        called.

        If any instance of me is using the Agg renderer, all instances
        will.
        """
        mpl = importlib.import_module("matplotlib")
        if useAgg and not cls.usingAgg:
            mpl.use('Agg')
            cls.usingAgg = True
        else:
            try:
                raise Exception(
                    "Neither GTK3Agg nor PyQt5Agg actually work consistently")
                mpl.use('GTK3Agg')
            except:
                try:
                    mpl.use('tkagg')
                except:
                    print("WARNING: Neither GTK3Agg nor tkagg available!")
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
            
    def __init__(self, *args, **kw):
        """
        Constructor possibilities (not including keywords, except I{Nc}):
        
        C{Plotter(Nc, Nr)}: Specify I{Nc} columns and I{Nr} rows.
        
        C{Plotter(N)}: Specify up to I{N} subplots in optimal
        arrangement of columns and rows.

        C{Plotter(N, Nc=x)}: Specify up to I{N} columns subplots with
        I{x} columns.
        
        C{Plotter(Nc, Nr, V)}: Specify I{Nc} columns and I{Nr} rows,
        with container object I{V}.

        C{Plotter(Nc, Nr, V)}: Specify up to I{N} subplots in optimal
        arrangement of columns and rows, with container object I{V}.

        C{Plotter(N, V, Nc=x)}: Specify up to I{N} columns subplots
        with I{x} columns, with container object I{V}.

        @keyword filePath: Specify the path of a PNG file to be
            created instead of a plot window being opened. (Implies
            I{useAgg}.)

        @keyword useAgg: Set C{True} to use the "Agg" backend, which
            works better for creating image files. If you're going to
            specify it for multiple plot images, do so the first time
            an instance of me is constructed.

        @keyword figSize: Set to a 2-sequence with figure width and
            height if not using the default, which is just shy of your
            entire monitor size. Dimensions are in inches, converted
            to pixels at 100 DPI, unless both are integers and either
            exceeds 75. Then they are considered to specify the pixel
            dimensions directly.

        @keyword width: Specify the figure width part of I{figSize}.
        
        @keyword height: Specify the figure height part of I{figSize}.

        @keyword h2: A single index, or a sequence or set containing
            one or more indices, of any rows (starting with 0 for the
            top row) that have twice the normal height. If an invalid
            index is included, an exception will be raised.
    
        @keyword w2: A single index, or a sequence or set containing
            one or more indices, of any columns (starting with 0 for
            the left column) that have twice the normal width. If an
            invalid index is included, an exception will be raised.
        """
        args, kw, N, self.Nc, self.Nr = self.parseArgs(*args, **kw)
        self.V = args[0] if args else None
        self.opts = Opts()
        self.filePath = kw.pop('filePath', None)
        if 'verbose' in kw: self.verbose = kw.pop('verbose')
        useAgg = bool(self.filePath) or kw.pop('useAgg', False)
        self.setupClass(useAgg=useAgg)
        figSize = kw.pop('figSize', self.figSize)
        if figSize is None:
            if useAgg or screeninfo is None:
                figSize = [10.0, 7.0]
            else:
                si = screeninfo.screeninfo.get_monitors()[0]
                figSize = [
                    float(x)/self.DPI for x in (si.width-80, si.height-80)]
        width = kw.pop('width', None)
        if width: figSize[0] = width
        height = kw.pop('height', None)
        if height: figSize[1] = height
        figSize = self._maybePixels(figSize)
        self.fig = self.plt.figure(figsize=figSize)
        self.figSize = figSize
        self.sp = Subplotter(
            self, N, self.Nc, self.Nr, kw.pop('h2', []), kw.pop('w2', []))
        # The ID is an integer, not a reference to anything
        self.ID = self.ph.add(self)
        self.kw = kw
        self.dims = Dims()
        self.xlabels = {}
        self.annotators = {}
        self.adj = Adjuster(self)
        self.reset()

    @staticmethod
    def parseArgs(*args, **kw):
        """
        Parse the supplied I{args} and I{kw} for a constructor call.

        Returns a 5-tuple with a revised args list and kw dict, the
        number of subplots, the number of columns, and the number of
        rows.
        """
        N = args[0]
        args = list(args[1:])
        Nc = kw.pop('Nc', None)
        if args and isinstance(args[0], int):
            # Nc, Nr specified
            if Nc:
                raise ValueError(
                    "You can't specify Nc as both a second arg and keyword")
            Nc = N
            Nr = args.pop(0)
            N = Nc*Nr
        else:
            # N specified
            Nc = Nc if Nc else 3 if N > 6 else 2 if N > 3 else 1
            Nr = int(np.ceil(float(N)/Nc))
        return args, kw, N, Nc, Nr
        
    def reset(self):
        """
        Clears everything out to start fresh.
        """
        self.dims.clear()
        self.xlabels.clear()
        self.annotators.clear()
        self._figTitle = None
        self.tbmTitle = None
        self._isSubplot = False
        self._universal_xlabel = False
        self._plotter = None
        self.Nsp = 0

    def __del__(self):
        """
        Safely ensures that I am removed from the class-wide I{ph}
        instance of L{PlotterHolder}.
        """
        # Only an integer is passed to the call
        self.ph.remove(self.ID)
        # No new references were created, nothing retained

    def _maybePixels(self, figSize):
        """
        Considers the supplied I{figSize} to be in pixels if both its
        elements are integers and at least one of them exceeds 75. In
        that case, scales it down by DPI.

        Returns the figSize in inches.
        """
        bigDim = False
        newFigSize = []
        for dim in figSize:
            if not isinstance(dim, int):
                # Not both integers, use original
                return figSize
            if dim > 75: bigDim = True
            # Convert from (presumed) pixels to Matplotlib's stupid inches
            newFigSize.append(float(dim)/self.DPI)
        # Use the converted dims unless neither was > 75
        return newFigSize if bigDim else figSize
    
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
    
    def __getattr__(self, name):
        """
        You can access plotting methods and a given subplot's plotting
        options as attributes.

        If you request a plotting method, you'll get an instance of me
        with my I{_plotter} method set to I{name} first.
        """
        if name in PLOTTER_NAMES:
            self._plotter = name
            return self
        if name in self.opts:
            return self.opts[name]
        raise AttributeError(sub(
            "No plotting option or attribute '{}'", name))
        
    def __enter__(self):
        """
        Upon an outer context entry, sets up the first subplot with
        cleared axes, preserves a copy of my global options, and
        returns a reference to myself as a subplotting tool.
        """
        # TODO: Allow my instance to be context-called again
        #self.reset()
        self.sp.setup()
        self._isSubplot = True
        self.opts.newLocal()
        return self

    def __exit__(self, *args):
        """
        Upon completion of context, turns minor ticks and grid on if
        enabled for this subplot's axis, restores global (all
        subplots) options.

        If the Agg rendererer is not being used (for generating PNG
        files), also sets a hook to adjust the subplot spacings and
        annotation positions upon window resizing.

        The args are just placeholders for the three args that
        C{contextmanager} supplies at the end of context: I{exc_type},
        I{exc_val}, I{exc_tb}. (None are useful here.)
        
        @see: L{_doPlots}.
        """
        # Do the last (and perhaps only) call's plotting
        self._doPlots()
        self._isSubplot = False
        self.opts.goGlobal()
        if not self.usingAgg:
            self.fig.canvas.mpl_connect('resize_event', self.subplots_adjust)

    def start(self):
        """
        An alternative to the context-manager way of using me. Just call
        this method and a reference to myself as a subplotting tool
        will be returned.

        Call L{done} when finished, which is the same thing as exiting
        my subplotting context.
        """
        if self._isSubplot:
            raise Exception("You are already in a subplotting context!")
        return self.__enter__()

    def done(self):
        """
        Call this after a call to L{start} when done plotting. This is the
        alternative to the context-manager way of using me.

        B{Note}: If you don't call this to close out a plotting
        session with the alternative method, the last subplot will not
        get drawn!

        @see: L{start}, which gets called to start the
            alternative-method plotting session.
        """
        if not self._isSubplot:
            raise Exception("You are not in a subplotting context!")
        self.__exit__()
            
    def subplots_adjust(self, *args):
        """
        Adjusts spacings.
        """
        dimThing = args[0] if args else self.fig.get_window_extent()
        fWidth, fHeight = [getattr(dimThing, x) for x in ('width', 'height')]
        self.adj.updateFigSize(fWidth, fHeight)
        if self._figTitle:
            kw = {
                'm': 10,
                'fontsize': self.fontsize('title', 14),
                'alpha': 1.0,
                'fDims': (fWidth, fHeight),
            }
            ax = self.fig.get_axes()[0]
            if self.tbmTitle: self.tbmTitle.remove()
            self.tbmTitle = TextBoxMaker(self.fig, **kw)("N", self._figTitle)
            titleObj = self.tbmTitle.tList[0]
        else: self.tbmTitle = titleObj = None
        kw = self.adj(self._universal_xlabel, titleObj)
        try:
            self.fig.subplots_adjust(**kw)
        except ValueError as e:
            if self.verbose:
                print((sub(
                    "WARNING: ValueError '{}' doing subplots_adjust({})",
                    e.message, ", ".join(
                        [sub("{}={}", x, kw[x]) for x in kw]))))
        self.updateAnnotations()
    
    def updateAnnotations(self, annotator=None):
        """
        Updates the positions of all annotations in an already-drawn plot.

        When L{PlotHelper} calls this, it will supply the annotator
        for its subplot.
        """
        plt = self.plt
        updated = False
        if annotator is None:
            for annotator in self.annotators.values():
                if annotator.update():
                    updated = True
        elif annotator.update(): updated = True
        if updated:
            # This raises a warning with newer matplotlib
            #plt.pause(0.0001)
            plt.draw()
        
    def _doPlots(self):
        """
        This gets called by L{__call__} at the beginning of each call to
        my subplot-context instance, and by L{__exit__} when subplot
        context ends, to do all the plotting for the previous subplot.

        Adds minor ticks and a grid, depending on the subplot-specific
        options. Then calls L{Opts.newLocal} on my I{opts} to create a
        new set of local options.
        """
        ax = self.sp.ax
        if ax: ax.helper.doPlots()
        # Setting calls now use new local options
        self.opts.newLocal()
    
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
                print((sub(proto, e.message, self.width, self.height)))
        self.subplots_adjust()
        # Calling plt.draw massively slows things down when generating
        # plot images on Rpi. And without it, the (un-annotated) plot
        # still updates!
        if False and self.annotators:
            # This is not actually run, see above comment
            self.plt.draw()
            for annotator in list(self.annotators.values()):
                if self.verbose: annotator.setVerbose()
                annotator.update()
        if fh is None:
            if not filePath:
                filePath = self.filePath
            if filePath:
                fh = open(filePath, 'wb+')
        if fh is None:
            self.plt.draw()
            if windowTitle: self.fig.canvas.set_window_title(windowTitle)
            if self.fc is not None: self.fc.draw()
            elif not noShow: self.plt.show()
        else:
            self.fig.savefig(fh, format='png')
            self.plt.close()
            if filePath is not None:
                # Only close a file handle I opened myself
                fh.close()
        if not noShow: self.clear()

    def clear(self):
        """
        Clears my figure with all annotators and artist
        dimensions. Removes my ID from the class-wide
        L{PlotterHolder}.
        """
        try:
            # This causes stupid errors with tkagg, so just wrap it in
            # try-except for now
            self.fig.clear()
        except: pass
        self.annotators.clear()
        self.dims.clear()
        self.ph.remove(self.ID)
            
    def xBounds(self, *args, **kw):
        """
        See L{Subplotter.xBounds}.
        """
        self.sp.xBounds(*args, **kw)
    
    def yBounds(self, *args, **kw):
        """
        See L{Subplotter.yBounds}.
        """
        self.sp.yBounds(*args, **kw)

    def fontsize(self, name, default=None):
        return self.opts['fontsizes'].get(name, default)

    def doKeywords(self, kVector, kw):
        """
        Applies line style/marker/color settings as keywords for this
        vector, except for options already set with keywords.
        
        Then applies plot keywords set via the set_plotKeyword call
        and then, with higher priority, those set via the constructor,
        if they don't conflict with explicitly set keywords to this
        call which takes highest priority.

        Returns the new kw dict.
        """
        kw = self.opts.kwModified(kVector, kw)
        for thisDict in (self.kw, self.plotKeywords):
            for name in thisDict:
                if name not in kw:
                    kw[name] = thisDict[name]
        return kw
    
    def doSettings(self, k):
        """
        Does C{set_XXX} calls on the C{Axes} object for the subplot at
        index I{k}.
        """
        def bbAdd(textObj):
            dims = self.adj.tsc.dims(textObj)
            self.dims.setDims(k, name, dims)

        for name in self._settings:
            value = self.opts[name]
            if not value: continue
            fontsize = self.fontsize(name, None)
            kw = {'size':fontsize} if fontsize else {}
            bbAdd(self.sp.set_(name, value, **kw))
            if name == 'xlabel':
                self.xlabels[k] = value
                continue
        settings = self.opts['settings']
        for name in settings:
            bbAdd(self.sp.set_(name, settings[name]))
    
    def __call__(self, *args, **kw):
        """
        In the next (perhaps first) subplot, or one whose index is
        specified with keyword I{k}, plots the second supplied vector
        (and any further ones) versus the first.

        If you supply a container object that houses vectors and
        provides access to them as items as the first argument, you
        can supply vector names instead of the vectors themselves. The
        container object must evaluate C{b in a} as C{True} if it
        contains a vector with I{b}, and must return the vector with
        C{a[b]}.
        
        Many options can be set via the methods in L{OptsBase},
        including a title, a list of plot markers and linestyles, and
        a list of legend entries for the plots with those keywords.

        Set I{useLabels} to C{True} to have annotation labels pointing
        to each plot line instead of a legend, with text taken from
        the legend list.

        You can override my default plotter by specifying the name of
        another one with the I{plotter} keyword, e.g.,
        C{plotter="step"}. But the usual way to do that is to call the
        corresponding method of my instance, e.g., C{sp.step(X, Y)}.
        
        Any other keywords you supply to this call are supplied to the
        underlying Matplotlib plotting call. (B{NOTE:} This is a
        change from previous versions of Yampex where keywords to this
        method were used to C{set_X} the axes, e.g., C{ylabel="foo"}
        results in a C{set_ylabel("foo")} command to the C{axes}
        object, for this subplot only. Use the new L{OptsBase.set}
        command instead.)

        Returns a L{SpecialAx} wrapper object for the C{Axes} object
        created for the plot.
        
        If you want to do everything with the next subplot on your
        own, bit by bit, and only want a reference to its C{Axes}
        object (still with special treatment via L{SpecialAx}) just
        call this with no args.

        For low-level Matplotlib operations, you can access the
        underlying C{Axes} object via the returned L{SpecialAx}
        object's I{ax} attribute. But none of its special features
        will apply to what you do that way.

        @keyword k: Set this to the integer index of the subplot you
            want the supplied vectors plotted in if not in sequence.
        
        @see: L{_doPlots}.
        """
        # Do plotting for the previous call (if any)
        self._doPlots()
        if 'plotter' not in kw:
            plotter = self._plotter
            self._plotter = None
        if plotter: kw.setdefault('plotter', plotter)
        k = kw.pop('k', None)
        ax = self.sp[k]
        ax.helper.addCall(args, kw)
        self.Nsp += 1
        return ax

