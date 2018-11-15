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

from yampex.annotate import Annotator, TextBoxMaker
from yampex.subplot import Subplotter
from yampex.scaling import Scaler
from yampex.util import sub


class OptsBase(object):
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

    def set_zeroLine(self, yes=True):
        """
        Adds a horizontal line at y=0 if the Y-axis range includes zero,
        unless called with C{False}.
        """
        self.opts['zeroLine'] = yes
        
    def add_marker(self, x):
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
        """
        self.opts['markers'].append(x)

    def add_line(self, x=None):
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

        If no line style character or C{None} is supplied, clears the
        list of line styles.
        """
        if x is None:
            self.opts['linestyles'] = []
            return
        self.opts['linestyles'].append(x)
    
    def set_yscale(self, x):
        """
        Manually sets the y-axis scaling.
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

        You may include a text prototype with format-substitution args
        following it, or just supply the final text string with no
        further arguments.
        """
        try:
            text = sub(proto, *args)
        except:
            # Probably called with kVector as a third argument, per
            # API of commit 15c49b and earlier
            text = proto
            kVector = args[0]
        else:
            kVector = kw.get('kVector', 0)
        self.opts['annotations'].append((k, text, kVector))

    def clear_annotations(self):
        """
        Clears the list of annotations.
        """
        self.opts['annotations'] = []

    def add_textBox(self, quadrant, text):
        """
        """
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
        else:
            self._isFigTitle = True
            self.fig.suptitle(text)

    def set_fontsize(self, name, fontsize):
        """
        Sets the I{fontsize} of the specified artist I{name}. Recognized
        names are 'legend' and 'annotations'.
        """
        self.opts['fontsizes'][name] = fontsize


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

    Construct an instance of me with the total number of subplots (to
    be intelligently apportioned into one or more rows and columns)
    or, with two constructor arguments, the number of columns followed
    by the number of rows.

    With the I{filePath} keyword, you can specify the file path of a
    PNG file for me to create or overwrite with each call to L{show}.
    
    You can set the I{width} and I{height} of the Figure in inches
    (100 DPI) with constructor keywords.

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
    figSize = (10.0, 7.0)
    colors = ['b', 'g', 'r', '#40C0C0', '#C0C040', '#C040C0', '#8080FF']
    timeScales = [
        (1E-9, "nanoseconds"),
        (1E-6, "microseconds"),
        (1E-3, "milliseconds"),
    ]

    _opts = {
        'settings':             {},
        'plotKeywords':         {},
        'marker':               '',
        'linestyle':            '-',
        'markers':              [],
        'linestyles':           [],
        'grid':                 False,
        'firstVectorTop':       False,
        'loglog':               False,
        'semilogx':             False,
        'semilogy':             False,
        'bar':                  False,
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

    @classmethod
    def useAgg(cls):
        if not getattr(cls, '_usingAgg', False):
            mpl = importlib.import_module("matplotlib")
            mpl.use('Agg')
            cls._usingAgg = True
    
    def __init__(self, N, *args, **kw):
        args = list(args)
        if args:
            Nx = N
            Ny = args.pop(0)
        else:
            Nx = self.N_cols(N)
            Ny = int(np.ceil(float(N)/Nx))
        self.V = args[0] if args else None
        self.opts = deepcopy(self._opts)
        self.filePath = kw.pop('filePath', None)
        if self.filePath or kw.pop('useAgg', False):
            self.useAgg()
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
        self._isSubplot = False
        self._an_xlabel_was_set = False
        self._universal_xlabel = False

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
    
    def show(self, windowTitle=None, fh=None, filePath=None):
        """
        Call this to show the figure with suplots after the last call to
        my instance.
        
        If I have a I{fc} attribute (which must reference an instance of
        Qt's C{FigureCanvas}, then the FigureCanvas is drawn instead
        of PyPlot doing a window show.

        You can supply an open file-like object for PNG data to be
        written to (instead of a Matplotlib Figure being displayed)
        with the I{fh} keyword. (It's up to you to close the file
        object.)

        Or, with the I{filePath} keyword, you can specify the file
        path of a PNG file for me to create or overwrite. (That
        overrides any I{filePath} you set in the constructor.)
        """
        self.fig.tight_layout()
        kw = {}
        if self._isFigTitle:
            kw['top'] = 0.93
        if self._an_xlabel_was_set:
            kw['hspace'] = 0.16
        try:
            self.fig.subplots_adjust(**kw)
        except ValueError as e:
            print sub(
                "WARNING: ValueError '{}' doing subplots_adjust({})",
                e.message,
                ", ".join([sub("{}={}", x, kw[x]) for x in kw]))
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
            if hasattr(self, 'fc'):
                self.fc.draw()
            else: self.plt.show()
            return
        self.fig.savefig(fh, format='png')
        self.plt.close()
        if filePath is not None:
            # Only close a file handle I opened myself
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

    def pickPlotter(self, ax, plotter, kw):
        bogusMap = {
            'bar': ('marker', 'linestyle', 'scaley'),
            'step': ('marker', 'linestyle', 'scaley'),
        }
        for name in ('loglog', 'semilogx', 'semilogy', 'bar', 'step', 'error'):
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
            kw['marker'] = getLast(self.markers, k) \
                if self.markers else self.marker
            kw['linestyle'] = getLast(self.linestyles, k) \
                if self.linestyles else self.linestyle
            if kw['marker'] in (',', '.'): kw['linestyle'] = ''
            if kw['linestyle'] == '-': kw['linewidth'] = 2
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
                else: ax.set_ylim(0, axFirst.get_ylim()[1]/yscale)
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
            if self.zeroLine:
                y0, y1 = axFirst.get_ylim()
                if y0 < 0 and y1 > 0:
                    axFirst.axhline(
                        y=0, linestyle='--',
                        linewidth=1, color="black", zorder=10)
            if self.legend and not self.annotations and not self.useLabels:
                axFirst.legend(*lineInfo, **{
                    'loc': "best",
                    'fontsize': self.fontsizes.get('legend', "small")})

        def doSettings():
            for name in self._settings:
                if self.opts[name]:
                    if name == 'xlabel':
                        if self._universal_xlabel:
                            if not self.sp.atBottom(): continue
                        else: self._an_xlabel_was_set = True
                    self.sp.set_(name, self.opts[name])
            for name in self.settings:
                self.sp.set_(name, self.settings[name])

        def doAnnotations(yscale):
            self.plt.draw()
            annotator = self.annotators[axFirst] = Annotator(
                axList, [firstVector]+list(vectors[1:]),
                fontsize=self.fontsizes.get('annotations', 'small'))
            for k, text, kVector in self.annotations:
                x = firstVector[k]
                y = vectors[kVector+1][k]
                kAxis = 0 if yscale is None or kVector == 0 else 1
                if isinstance(text, int):
                    text = sub("{:d}", text)
                elif isinstance(text, float):
                    text = sub("{:.2f}", text)
                annotator(kAxis, x, y, text)
                annotator.update()
                
        ax = axFirst = self.sp[None]
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
        doSettings()
        if not args:
            axList = [ax]
        else:
            lineInfo = [[], []]
            yscale = self.yscale
            vectors, names, V = self.parseArgs(args)
            firstVector = self.scaleTime(vectors)
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
                tbm = TextBoxMaker(axFirst)
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
                print sub("No annotator for axes object '{}'", repr(ax))
                import pdb; pdb.set_trace()
        return self.annotators[ax]
        
