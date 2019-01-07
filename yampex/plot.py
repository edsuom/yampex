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

import weakref
from copy import deepcopy
import importlib

import screeninfo

import numpy as np

from yampex.annotate import Annotator, TextBoxMaker
from yampex.subplot import Subplotter
from yampex.scaling import Scaler
from yampex.util import sub


class PlotterHolder(object):
    def __init__(self):
        self.pDict = weakref.WeakValueDictionary()

    def add(self, obj):
        ID = id(obj)
        self.pDict[ID] = obj
        return ID

    def remove(self, ID):
        if ID in self.pDict:
            del self.pDict[ID]

    def removeAll(self):
        self.pDict.clear()
            
    def doForAll(self, methodName, *args, **kw):
        """
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


class OptsBase(object):
    """
    I am an abstract base class with the option setting methods of the
    L{Plotter}.
    """
    def set(self, name, value):
        """
        Before this subplot is drawn, do a C{set_name=value} command to the
        axes. You can call this method as many times as you like with
        a different attribute I{name} and I{value}.

        Use this method in place of calling the Plotter instance with
        keywords. Now, such keywords are sent directly to the
        underlying Matplotlib plotting call.
        """
        self.opts['settings'][name] = value

    def add_plotKeyword(self, name, value):
        """
        Add a keyword to the underlying Matplotlib plotting call.
        """
        self.opts['plotKeywords'][name] = value

    def clear_plotKeywords(self):
        """
        Clears all keywords for this subplot.
        """
        self.opts['plotKeywords'].clear()
        
    def set_loglog(self, yes=True):
        """
        Makes both axes logarithmic, unless called with C{False}.
        """
        self.opts['loglog'] = yes

    def set_semilogx(self, yes=True):
        """
        Makes x-axis logarithmic, unless called with C{False}.
        """
        self.opts['semilogx'] = yes

    def set_semilogy(self, yes=True):
        """
        Makes y-axis logarithmic, unless called with C{False}.
        """
        self.opts['semilogy'] = yes
        
    def set_bar(self, yes=True):
        """
        Specifies a bar plot, unless called with C{False}.
        """
        self.opts['bar'] = yes

    def set_stem(self, yes=True):
        """
        Specifies a stem plot, unless called with C{False}.
        """
        self.opts['stem'] = yes

    def set_step(self, yes=True):
        """
        Specifies a step plot, unless called with C{False}.
        """
        self.opts['step'] = yes
        
    def set_error(self, yes=True):
        """
        Specifies an error bar plot, unless called with C{False}.

        B{TODO:} Not yet supported.
        """
        self.opts['error'] = yes
        
    def set_useLabels(self, yes=True):
        """
        Has annotation labels point to each plot line instead of a legend,
        with text taken from the legend list. Call with C{False} to
        revert to default legend-box behavior.
        """
        self.opts['useLabels'] = yes

    def set_grid(self, yes=True):
        """
        Adds a grid, unless called with C{False}.
        """
        self.opts['grid'] = yes

    def set_timex(self, yes=True):
        """
        Uses intelligent time scaling for the x-axis, unless called with
        C{False}.
        """
        self.opts['timex'] = yes
        if not self._isSubplot:
            self._universal_xlabel = True

    def set_firstVectorTop(self):
        """
        Has the first dependent vector (the second argument to the
        L{Plotter} object call) determine the top (maximum) of the
        displayed plot boundary.
        """
        self.opts['firstVectorTop'] = True
        
    def set_bump(self, yes=True):
        """
        If you don't manually set a yscale with a call to L{set_yscale},
        you can call this method to bump the common y-axis upper limit
        to 120% of what Matplotlib decides. Call with C{False} to
        disable the bump.
        """
        self.opts['bump'] = yes

    def set_zeroBottom(self, yes=True):
        """
        Sets the bottom (minimum) of the Y-axis range to zero, unless
        called with C{False}. This is useful for plotting values that
        are never negative and where zero is a meaningful absolute
        minimum.
        """
        self.opts['zeroBottom'] = yes

    def set_zeroLine(self, y=0):
        """
        Adds a horizontal line at the specified I{y} value (default is
        y=0) if the Y-axis range includes that value. If y is C{None}
        or C{False}, clears any previously set line.
        """
        self.opts['zeroLine'] = y
        
    def add_marker(self, x, size=None):
        """
        Appends the supplied marker style character to the list of markers
        being used. The first and possibly only marker in the list
        applies to the first vector plotted within a given subplot. If
        there is an additional vector being plotted within a given
        subplot (three or more arguments supplied when calling the
        L{Plotter} object, and more than one marker has been added to
        the list, then the second marker in the list is used for that
        second vector plot line. Otherwise, the first (only) marker in
        the list is used for the second plot line as well.

        You can specify a I{size} for the marker as well.
        """
        self.opts['markers'].append((x, size))

    def add_line(self, x=None, width=None):
        """
        Appends the supplied line style character to the list of line
        styles being used. The first and possibly only line style in
        the list applies to the first vector plotted within a given
        subplot. If there is an additional vector being plotted within
        a given subplot (three or more arguments supplied when calling
        the L{Plotter} object, and more than one line style has been
        added to the list, then the second line style in the list is
        used for that second vector plot line. Otherwise, the first
        (only) line style in the list is used for the second plot line
        as well.

        You can specify a I{width} for the line as well.
        
        If no line style character or C{None} is supplied, clears the
        list of line styles.
        """
        if x is None:
            self.opts['linestyles'] = []
            return
        self.opts['linestyles'].append((x, width))
    
    def set_yscale(self, x=True):
        """
        Rescales the plotted height of all vectors after the first
        dependent one to be plotted, relative to that first dependent
        one, by setting a y scale for it. The result is two different
        twinned x-axes (one for the first dependent vector and one for
        everybody else) and a different y-axis label on the right.

        Use a scale > 1 if the second (and later) vectors are bigger
        than the first and you want to expand the right-hand scale.

        Use a scale < 1 if the second (and later) vectors are smaller
        than the first and you the right-hand scale to be shrunk.

        Use C{True} for the argument to have the scaling done
        automatically. (This is the default.)
        """
        self.opts['yscale'] = x

    def _axisOpt(self, optName, axisName, value=None):
        axisName = axisName.lower()
        if axisName not in "xy":
            raise ValueError(sub("Invalid axisName '{}'", axisName))
        if value is None:
            return self.opts[optName].setdefault(axisName, {})
        self.opts[optName][axisName] = value
        
    def set_axisExact(self, axisName, yes=True):
        """
        Forces the limits of the named axis ("x" or "y") to exactly the
        data range, unless called with C{False}.
        """
        self._axisOpt('axisExact', axisName, yes)
        
    def set_tickSpacing(self, axisName, major, minor=None):
        """
        Sets the major tick spacing for I{axisName} ("x" or "y"), and
        minor tick spacing as well. For each setting, an C{int} will
        set a maximum number of tick intervals, and a C{float} will
        set a spacing between intervals.

        You can set I{minor} C{True} to have minor ticks set
        automatically, or C{False} to have them turned off. (Major
        ticks are set automatically by default, and cannot be turned
        off.)
        """
        ticks = self._axisOpt('ticks', axisName)
        ticks['major'] = major
        if minor is not None:
            ticks['minor'] = minor

    def set_minorTicks(self, axisName, yes=True):
        """
        """
        self._axisOpt('ticks', axisName)['minor'] = yes
        
    def set_axvline(self, k):
        """
        Adds a vertical dashed line at the data point with integer index
        I{k}. To set it to an x value, use a float.
        """
        self.opts['axvlines'].append(k)
        
    def set_xlabel(self, x):
        """
        Sets the x-axis label. (Ignored if time-x mode has been activated
        with a call to L{set_timex}.)

        If called out of context, on the Plotter instance, this
        x-label is used for all subplots and only appears in the last
        (bottom) subplot of each column of subplots.
        """
        self.opts['xlabel'] = x
        if not self._isSubplot:
            self._universal_xlabel = True

    def set_ylabel(self, x):
        """
        Sets the y-axis label.
        """
        self.opts['ylabel'] = x

    def add_legend(self, proto, *args):
        """
        Adds the supplied format-substituted text to the list of legend
        entries. You may include a text I{proto}type with
        format-substitution I{args}, or just supply the final text
        string with no further arguments.
        """
        text = sub(proto, *args)
        self.opts['legend'].append(text)

    def clear_legend(self):
        """
        Clears the list of legend entries.
        """
        self.opts['legend'] = []

    def set_legend(self, *args, **kw):
        """
        Sets the list of legend entries. Supply a list of legend entries,
        either as a single argument or with one entry per argument.

        You can set the I{fontsize} keyword to the desired fontsize of
        the legend. The default is 'small'.
        """
        if len(args) == 1 and hasattr(args[0], '__iter__'):
            args = args[0]
        self.opts['legend'] = list(args)
        if 'fontsize' in kw:
            self.opts['fontsizes']['legend'] = kw['fontsize']
    
    def add_annotation(self, k, proto, *args, **kw):
        """
        Adds the text supplied after index I{k} at an annotation of the
        plotted vector. If there is more than one vector being plotted
        within the same subplot, you can have the annotation refer to
        a vector other than the first one by setting the keyword
        I{kVector} to its non-zero index.

        The annotation points to the point at index I{k} of the
        plotted vector, unless I{k} is a float. In that case, it
        points to the point where the vector is closest to that float
        value.
        
        You may include a text prototype with format-substitution args
        following it, or just supply the final text string with no
        further arguments.

        You can set the annotation to the first y-axis value that
        crosses a float value of I{k} by setting I{y} C{True}.
        """
        kVector = None
        if args:
            if "{" not in proto:
                # Called with kVector as a third argument, per API of
                # commit 15c49b and earlier
                text = proto
                kVector = args[0]
            else: text = sub(proto, *args)
        else:  text = proto
        if kVector is None:
            kVector = kw.get('kVector', 0)
        y = kw.get('y', False)
        self.opts['annotations'].append((k, text, kVector, y))

    def clear_annotations(self):
        """
        Clears the list of annotations.
        """
        self.opts['annotations'] = []

    def add_textBox(self, quadrant, proto, *args):
        """
        """
        text = sub(proto, *args)
        prevText = self.opts['textBoxes'].get(quadrant, None)
        if prevText:
            text = prevText + "\n" + text
        self.opts['textBoxes'][quadrant] = text
        
    def clear_textBoxes(self):
        """
        Clears the dict of text boxes.
        """
        self.opts['textBoxes'].clear()
        
    def set_title(self, proto, *args):
        """
        Sets a title for all subplots (if called out of context) or for
        just the present subplot (if called in context). You may
        include a text I{proto}type with format-substitution I{args},
        or just supply the final text string with no further
        arguments.
        """
        text = sub(proto, *args)
        if self._isSubplot:
            self.opts['title'] = text
        else: self._figTitle = text

    def set_fontsize(self, name, fontsize):
        """
        Sets the I{fontsize} of the specified artist I{name}. Recognized
        names are 'legend' and 'annotations'.
        """
        self.opts['fontsizes'][name] = fontsize


class SpecialAx(object):
    """
    I pretend to be a C{matplotlib.Axes} object except that I
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

    Construct an instance of me with the total number of subplots (to
    be intelligently apportioned into one or more rows and columns)
    or, with two constructor arguments, the number of columns followed
    by the number of rows.

    With the I{filePath} keyword, you can specify the file path of a
    PNG file for me to create or overwrite with each call to L{show}.
    
    You can set the I{width} and I{height} of the Figure in inches
    (100 DPI) with constructor keywords, and (read-only) access them
    via my properties of the same names. Or set my I{figSize}
    attribute (in a subclass or with that constructor keyword) to a
    2-sequence with figure width and height in inches. The default
    width and height is just shy of the entire monitor size.

    Use the "Agg" backend by supplying the keyword I{useAgg} or
    calling the L{useAgg} class method. This works better for plotting
    to an image file, and is selected automatically if you supply a
    I{filePath} to the constructor. Be aware that, once selected, that
    backend will be used for all instances of me. If you're using the
    "Agg" backend, you should specify it the first time an instance is
    constructed, or beforehand with the L{useAgg} class method.
    
    Any other keywords you supply to the constructor are supplied to
    the underlying Matplotlib plotting call for all
    subplots. (B{NOTE:} This is a change from previous versions of
    Yampex where constructor keywords were used to C{set_X} the axes,
    e.g., C{ylabel="foo"} results in a C{set_ylabel("foo")} command to
    the C{axes} object, for all subplots. Use the new L{OptsBase.set}
    command instead, before the context call.)
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
        if useAgg and not getattr(cls, '_usingAgg', False):
            mpl = importlib.import_module("matplotlib")
            mpl.use('Agg')
            cls._usingAgg = True
        if not getattr(cls, 'plt', None):
            cls.plt = importlib.import_module("matplotlib.pyplot")
    
    def __init__(self, N, *args, **kw):
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
        return self.fig.get_figwidth()
    @property
    def height(self):
        return self.fig.get_figheight()
        
    def __nonzero__(self):
        return bool(len(self.sp))
        
    def __getattr__(self, name):
        return self.opts[name]
        
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
        self.opts = deepcopy(self.global_opts)            

    @classmethod
    def showAll(cls):
        OK = cls.ph.doForAll('show', noShow=True)
        if OK: cls.plt.show()
        cls.ph.doForAll('clear')
        # They should all have removed themselves now, but what the
        # heck, clear it anyways
        cls.ph.removeAll()

    def subplots_adjust(self, **kw):
        """
        Calls C{subplots_adjust} on my figure, doing a bit of tweaking
        first.
        """
        def wSpacing(pts):
            return 0.18*pts / (self.fig.get_figwidth() + 5)
        
        w = wSpacing(12)
        kw.setdefault('wspace', w)
        kw.setdefault('left', 0.5*w)
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
        def letterHeight(x):
            h = x.get_size() / 72
            h *= 3.0 / self.fig.get_figheight() + 0.05
            return h
        
        try:
            self.fig.tight_layout()
        except ValueError as e:
            if self.verbose:
                proto = "WARNING: ValueError '{}' doing tight_layout "+\
                        "on {:.5g} x {:.5g} figure"
                print(sub(proto, e.message, self.width, self.height))
        kw = {}
        if self._figTitle:
            kw['top'] = 1.0 - letterHeight(self.fig.suptitle(self._figTitle))
        universal_xlabel = self._universal_xlabel
        if universal_xlabel:
            # Thanks to kennytm,
            # https://stackoverflow.com/questions/3844801/
            #  check-if-all-elements-in-a-list-are-identical
            if len(set(self._xlabels.values())) > 1:
                universal_xlabel = False
        betweenSmaller = True
        bottomBigger = False
        textObj = None
        for k in self._xlabels:
            if self.sp.atBottom(k):
                # Bottom subplot
                bottomBigger = True
            else:
                if universal_xlabel: continue
                betweenSmaller = False
            ax = self.sp.axes[k]
            textObj = ax.set_xlabel(self._xlabels[k])
        if textObj:
            h = letterHeight(textObj)
            height = self.sp.Nr * h
            height *= 1.1 if betweenSmaller else 1.8
            kw['hspace'] = height
            if bottomBigger: kw['bottom'] = 11.0/(5+self.sp.Nr) * h
        if kw: self.subplots_adjust(**kw)
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
        self.ph.remove(self.ID)
            
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
            for name in self._settings:
                value = self.opts[name]
                if not value: continue
                if name == 'xlabel':
                    self._xlabels[self.sp.kLast] = value
                    continue
                self.sp.set_(name, value)
            for name in self.settings:
                self.sp.set_(name, self.settings[name])

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
        
