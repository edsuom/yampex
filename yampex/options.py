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
The L{Plotter} methods defined by its L{OptsBase} base class give
you a convenient API for setting tons of options for the next subplot.

Or, if you call your C{Plotter} instance outside the subplot in
context (before the C{with ... as} statement), calling these methods
defines options for all subplots.

Keep the API for L{OptsBase} handy, and maybe a copy of the
U{source<http://edsuom.com/yampex/yampex.options.py>} open in your
editor, as a handy reference for all the plotting options you can set.
"""

from copy import copy
from contextlib import contextmanager

from yampex.util import PLOTTER_NAMES, sub


class Opts(object):
    """
    I am a dict-like object of options. I make it easy to override
    global options with local ones just for the present subplot, and
    provide a few useful methods.

    @ivar go: A dict of global options that are set from my I{_opts}
        defaults and then from any option-setting calls to the
        L{OptsBase} subclass outside subplotting context.

    @ivar lo: A dict of local options that are set only from
        option-sitting calls inside the subplotting context, for the
        present subplot.
    """
    _colors = ['b', 'g', 'r', '#40C0C0', '#C0C040', '#C040C0', '#8080FF']
    _opts = {
        'colors':               [],
        'settings':             {},
        'plotKeywords':         {},
        'marker':               ('', None),
        'markers':              [],
        'linestyles':           [],
        'grid':                 False,
        'firstVectorTop':       False,
        'call':                 "plot",
        'autolegend':           False,
        'legend':               [],
        'annotations':          [],
        'textBoxes':            {},
        'xscale':               1.0,
        'yscale':               1.0,
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
        'zeroLine':             {},
        'fontsizes':            {},
    }

    def __init__(self):
        self.go = self._opts.copy()
        self.lo = None
        self.loList = []

    def __repr__(self):
        maybeMore = ""
        if self.lo in self.loList:
            maybeMore = sub(" for subplot #{:d}", self.loList.index(self.lo)+1)
        lines = [sub(
            "Options at {}{}: global (local)", hex(
                id(self)), maybeMore), "-"*50]
        for name in sorted(self.go.keys()):
            goVal = self.go[name]
            loVal = sub(" ({})", self.lo[name]) if name in self.lo else ""
            lines.append(sub("{:>18s}  {}{}", name, goVal, loVal))
        return "\n".join(lines)
        
    def __contains__(self, key):
        if key in self.go: return True
        if self.lo is None: return False
        return key in self.lo
    
    def __setitem__(self, key, value):
        if self.lo is None:
            self.go[key] = value
        else: self.lo[key] = value

    def __getitem__(self, key):
        if self.lo and key in self.lo:
            return self.lo[key]
        value = self.go[key]
        if self.lo is None:
            return value
        if isinstance(value, (list, dict)):
            value = copy(value)
            self.lo[key] = value
        return value

    def newLocal(self):
        """
        Sets a new local options context, appending it to my I{loList}.

        All option-setting calls to your L{OptsBase} subclass will now
        go to a new set of local options, and all option inquiries
        will start with the local options and then go to globals,
        ignoring all previously set local options.
        """
        self.lo = {}
        self.loList.append(self.lo)
        
    def useLocal(self, kSubplot):
        kMax = len(self.loList) - 1
        if kSubplot > kMax : kSubplot = kMax
        self.lo = self.loList[kSubplot]

    def usePrevLocal(self):
        k = -2 if len(self.loList) > 1 else -1
        self.lo = self.loList[k]
        
    def useLastLocal(self):
        self.lo = self.loList[-1]

    @contextmanager
    def prevLocal(self):
        """
        Lets you use my previous local options (or the current ones, if
        there are no previous ones) inside a context call.
        """
        self.usePrevLocal()
        yield
        self.useLastLocal()
        
    def goGlobal(self):
        """
        Sets my options context to global, where it began before the first
        call to L{newLocal}.

        Any further option-setting calls will affect global options,
        and any option inquiries will refer strictly to global
        options.
        """
        self.lo = None
        del self.loList[:]
        
    def getColor(self, k):
        """
        Supply an integer index starting from zero and this returns a
        color from a clean and simple default palette.
        """
        colors = self['colors']
        if not colors: colors = self._colors
        return colors[k % len(colors)]

    def getLast(self, key, k):
        """
        Assuming that I{key} refers to one of my options with a sequence
        value, returns its item at index I{k}, or its last item if the
        index is beyond its end.
        """
        obj = self[key]
        return obj[k] if k < len(obj) else obj[-1]

    def useLegend(self):
        """
        Returns C{True} if a legend should be added, given my current set
        of options.
        """
        if self['autolegend']: return True
        if not self['legend']: return
        return not self['useLabels']

    def kwModified(self, k, kw_orig):
        """
        Adds 'linestyle', 'linewidth', 'marker', and 'color' entries for
        the next plot to I{kw} if not already defined.

        Returns a new kw dict, leaving the original one alone.
        """
        def nd(*keys):
            """
            Returns C{True} if none of the I{keys} are defined in I{kw}.
            """
            for key in keys:
                if key in kw:
                    return False
            return True

        kw = kw_orig.copy()
        if self['markers']:
            marker, size = self.getLast('markers', k)
        else: marker, size = self['marker']
        if nd('marker'): kw['marker'] = marker
        if nd('markersize', 'ms') and size is not None:
            kw['markersize'] = size
        width = 2
        if nd('linestyle', 'ls'):
            if self['linestyles']:
                kw['linestyle'], width = self.getLast('linestyles', k)
            elif kw['marker'] in (',', '.'):
                kw['linestyle'] = ''
            else: kw['linestyle'] = '-'
        if nd('linewidth', 'lw'):
            kw['linewidth'] = width
        if nd('color', 'c'):
            color = self.getColor(k)
            kw['color'] = color
        return kw
    

class OptsBase(object):
    """
    I am an abstract base class with the option setting methods of the
    L{Plotter}.

    Keep the API for L{OptsBase} handy, and maybe a copy of the
    U{source<http://edsuom.com/yampex/yampex.options.py>} open in your
    editor, as a handy reference for all the plotting options you can
    set.

    @ivar opts: A dict of options.
    """
    def _axisOpt(self, optName, axisName, value=None):
        """
        Sets axis option I{optName} for axis I{axisName} (either "x" or
        "y") to I{value}. If no value supplied, returns a dict of the
        options that are currently set (empty if none).

        The axis options are in my I{opts} dict, keyed by option
        name. Each entry is a sub-dict with at most one entry per
        axis, keyed by axis name.
        """
        axisName = axisName.lower()
        if axisName not in "xy":
            raise ValueError(sub("Invalid axisName '{}'", axisName))
        if value is None:
            return self.opts[optName].setdefault(axisName, {})
        self.opts[optName][axisName] = value
        
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

    @contextmanager
    def prevOpts(self):
        """
        Lets you use my previous local options (or the current ones, if
        there are no previous ones) inside a context call.
        """
        self.opts.usePrevLocal()
        yield
        self.opts.useLastLocal()
        
    def add_annotation(self, k, proto, *args, **kw):
        """
        Adds the text supplied after index I{k} at an annotation of the
        plotted vector.

        If there is more than one vector being plotted within the same
        subplot, you can have the annotation refer to a vector other
        than the first one by setting the keyword I{kVector} to its
        non-zero index.

        The annotation points to the point at index I{k} of the
        plotted vector, unless I{k} is a float. In that case, it
        points to the point where the vector is closest to that float
        value.
        
        You may include a text prototype with format-substitution args
        following it, or just supply the final text string with no
        further arguments. If you supply just an integer or float
        value with no further arguments, it will be formatted
        reasonably.

        You can set the annotation to the first y-axis value that
        crosses a float value of I{k} by setting I{y} C{True}.

        @see: L{clear_annotations}.
        """
        kVector = None
        if args:
            if "{" not in proto:
                # Called with kVector as a third argument, per API of
                # commit 15c49b and earlier
                text = proto
                kVector = args[0]
            else: text = sub(proto, *args)
        elif isinstance(proto, int):
            text = sub("{:+d}", proto)
        elif isinstance(proto, float):
            text = sub("{:+.4g}", proto)
        else: text = proto
        if kVector is None:
            kVector = kw.get('kVector', 0)
        y = kw.get('y', False)
        self.opts['annotations'].append((k, text, kVector, y))
    
    def add_axvline(self, k):
        """
        Adds a vertical dashed line at the data point with integer index
        I{k}. You can use negative indices, e.g., -1 for the last data
        point.

        To place the dashed line at (or at least near) an x value, use
        a float for I{k}.
        """
        self.opts['axvlines'].append(k)

    def add_color(self, x=None):
        """
        Appends the supplied line style character to the list of colors
        being used.

        The first and possibly only color in the list applies to the
        first vector plotted within a given subplot. If there are
        additional vectors being plotted within a given subplot (three
        or more arguments supplied when calling the L{Plotter} object,
        more than the number of colors that have been added to the
        list, then the colors rotate back to the first one in the
        list.

        If you never call this and don't set your own list with a call
        to L{set_colors}, a default color list is used.

        If no color code or C{None} is supplied, reverts to the
        default color scheme.
        """
        if x is None:
            self.opts['colors'] = []
            return
        self.opts['colors'].append(x)

    def add_legend(self, proto, *args):
        """
        Adds the supplied format-substituted text to the list of legend
        entries.

        You may include a text I{proto}type with format-substitution
        I{args}, or just supply the final text string with no further
        arguments.

        @see: L{clear_legend}, L{set_legend}.
        """
        text = sub(proto, *args)
        self.opts['legend'].append(text)

    def add_line(self, *args, **kw):
        """
        Appends the supplied line style string(s) to my list of line
        styles being used.

        The first and possibly only line style in the list applies to
        the first vector plotted within a given subplot. If there is
        an additional vector being plotted within a given subplot
        (three or more arguments supplied when calling the L{Plotter}
        object, and more than one line style has been added to the
        list, then the second line style in the list is used for that
        second vector plot line. Otherwise, the first (only) line
        style in the list is used for the second plot line as well.

        If no line style character or C{None} is supplied, clears the
        list of line styles.
        
        @keyword width: A I{width} for the line(s). If you want
            separate line widths for different lines, call this
            repeatedly with each seperate line style and width. (You
            can make the width a second argument of a 2-arg call,
            after a single line style string.)
        
        """
        if not args or args[0] is None:
            self.opts['linestyles'] = []
            return
        if len(args) == 2 and not isinstance(args[1], str):
            width = args[1]
            args = [args[0]]
        else: width = kw.get('width', None)
        for x in args:
            self.opts['linestyles'].append((x, width))

    def add_lines(self, *args, **kw):
        """
        Alias for L{add_line}.
        """
        return self.add_line(*args, **kw)
            
    def add_marker(self, x, size=None):
        """
        Appends the supplied marker style character to the list of markers
        being used.

        The first and possibly only marker in the list applies to the
        first vector plotted within a given subplot. If there is an
        additional vector being plotted within a given subplot (three
        or more arguments supplied when calling the L{Plotter} object,
        and more than one marker has been added to the list, then the
        second marker in the list is used for that second vector plot
        line. Otherwise, the first (only) marker in the list is used
        for the second plot line as well.

        You can specify a I{size} for the marker as well.
        """
        self.opts['markers'].append((x, size))

    def add_plotKeyword(self, name, value):
        """
        Add a keyword to the underlying Matplotlib plotting call.

        @see: L{clear_plotKeywords}.
        """
        self.opts['plotKeywords'][name] = value

    def add_textBox(self, location, proto, *args):
        """
        Adds a text box to the specified I{location} of the subplot.

        Here are the locations (you can use the integer instead of the
        abbreviation if you want), along with their text alignments:

            1. "NE": right, top.

            2. "E": right, center.

            3. "SE": right, bottom.

            4. "S": center, bottom.

            5. "SW": left, bottom.

            6. "W": left, center.

            7. "NW": left, top.

            8. "N": center, top.

        If there's already a text box at the specified location, a
        line will be added to it.

        You may include a text I{proto}type with format-substitution
        I{args}, or just supply the final text string with no further
        arguments.

        @see: L{clear_textBoxes}.
        """
        text = sub(proto, *args)
        prevText = self.opts['textBoxes'].get(location, None)
        if prevText:
            text = prevText + "\n" + text
        self.opts['textBoxes'][location] = text

    
    def clear_annotations(self):
        """
        Clears the list of annotations.
        """
        self.opts['annotations'] = []

    def clear_legend(self):
        """
        Clears the list of legend entries.
        """
        self.opts['legend'] = []

    def clear_plotKeywords(self):
        """
        Clears all keywords for this subplot.
        """
        self.opts['plotKeywords'].clear()

    def clear_textBoxes(self):
        """
        Clears the dict of text boxes.
        """
        self.opts['textBoxes'].clear()
    
    
    def plot(self, call="plot"):
        """
        Specifies a non-logarithmic regular plot, unless called with the
        name of a different plot type.
        """
        if call not in PLOTTER_NAMES:
            raise ValueError(sub("Unrecognized plot type '{}'", call))
        self.opts['call'] = call

    def plot_bar(self, yes=True):
        """
        Specifies a bar plot, unless called with C{False}.
        """
        self.opts['call'] = "bar" if yes else "plot"

    def plot_error(self, yes=True):
        """
        Specifies an error bar plot, unless called with C{False}.
        """
        self.opts['call'] = "error" if yes else "plot"

    def plot_loglog(self, yes=True):
        """
        Makes both axes logarithmic, unless called with C{False}.
        """
        self.opts['call'] = "loglog" if yes else "plot"

    def plot_semilogx(self, yes=True):
        """
        Makes x-axis logarithmic, unless called with C{False}.
        """
        self.opts['call'] = "semilogx" if yes else "plot"

    def plot_semilogy(self, yes=True):
        """
        Makes y-axis logarithmic, unless called with C{False}.
        """
        self.opts['call'] = "semilogy" if yes else "plot"
        
    def plot_stem(self, yes=True):
        """
        Specifies a stem plot, unless called with C{False}.
        """
        self.opts['call'] = "stem" if yes else "plot"

    def plot_step(self, yes=True):
        """
        Specifies a step plot, unless called with C{False}.
        """
        self.opts['call'] = "step" if yes else "plot"

    
    def set_axisExact(self, axisName, yes=True):
        """
        Forces the limits of the named axis ("x" or "y") to exactly the
        data range, unless called with C{False}.
        """
        self._axisOpt('axisExact', axisName, yes)
        
    def set_axvline(self, k):
        """
        Adds a vertical dashed line at the data point with integer index
        I{k}.

        To set it to an x value, use a float for I{k}.

        @see: L{add_axvline}, the preferred form of this call.
        """
        print("WARNING: Only add_axvline will be supported in the future!")
        self.add_axvline(k)
        
    def set_colors(self, *args):
        """
        Sets the list of colors. Call with no args to clear the list and
        revert to default color scheme.

        Supply a list of color codes, either as a single argument or
        with one entry per argument.
        """
        if len(args) == 1 and hasattr(args[0], '__iter__'):
            args = args[0]
        self.opts['colors'] = list(args)
        
    def set_firstVectorTop(self):
        """
        Has the first dependent vector (the second argument to the
        L{Plotter} object call) determine the top (maximum) of the
        displayed plot boundary.
        """
        self.opts['firstVectorTop'] = True
        
    def set_fontsize(self, name, fontsize):
        """
        Sets the I{fontsize} of the specified artist I{name}.

        Recognized names are 'title', 'xlabel', 'ylabel', 'legend',
        'annotations', and 'textbox'.
        """
        self.opts['fontsizes'][name] = fontsize

    def set_grid(self, yes=True):
        """
        Adds a grid, unless called with C{False}.

        @see: L{use_grid}, the preferred form of this call.
        """
        print("WARNING: Only use_grid will be supported in the future!")
        self.use_grid(yes)

    def set_legend(self, *args, **kw):
        """
        Sets the list of legend entries.

        Supply a list of legend entries, either as a single argument
        or with one entry per argument. You can set the I{fontsize}
        keyword to the desired fontsize of the legend; the default is
        'small'.

        @see: L{add_legend}, L{clear_legend}.
        """
        if len(args) == 1 and hasattr(args[0], '__iter__'):
            args = args[0]
        self.opts['legend'] = list(args)
        if 'fontsize' in kw:
            self.opts['fontsizes']['legend'] = kw['fontsize']
    
    def set_minorTicks(self, axisName, yes=True):
        """
        Enables minor ticks for I{axisName} ("x" or "y"). Call with
        C{False} after the I{axisName} to disable.

        @see: L{use_minorTicks}, the preferred form of this call.
        """
        print("WARNING: Only use_minorTicks will be supported in the future!")
        self.use_minorTicks(axisName, yes)
        
    def set_tickSpacing(self, axisName, major, minor=None):
        """
        Sets the major tick spacing for I{axisName} ("x" or "y"), and
        minor tick spacing as well.

        For each setting, an C{int} will set a maximum number of tick
        intervals, and a C{float} will set a spacing between
        intervals.

        You can set I{minor} C{True} to have minor ticks set
        automatically, or C{False} to have them turned off. (Major
        ticks are set automatically by default, and cannot be turned
        off.)
        """
        ticks = self._axisOpt('ticks', axisName)
        ticks['major'] = major
        if minor is not None:
            ticks['minor'] = minor

    def set_timex(self, yes=True):
        """
        Uses intelligent time scaling for the x-axis, unless called with
        C{False}.

        @see: L{use_timex}, the preferred form of this call.
        """
        print("WARNING: Only use_timex will be supported in the future!")
        self.use_timex(yes)

    def set_title(self, proto, *args):
        """
        Sets a title for all subplots (if called out of context) or for
        just the present subplot (if called in context).

        You may include a text I{proto}type with format-substitution
        I{args}, or just supply the final text string with no further
        arguments.
        """
        text = sub(proto, *args)
        if self._isSubplot:
            self.opts['title'] = text
        else: self._figTitle = text

    def set_useLabels(self, yes=True):
        """
        Has annotation labels point to each plot line instead of a legend,
        with text taken from the legend list.

        Call with C{False} to revert to default legend-box behavior.

        @see: L{use_labels}, the preferred form of this call.
        """
        print("WARNING: Only use_labels will be supported in the future!")
        self.use_labels(yes)

    def set_xlabel(self, x):
        """
        Sets the x-axis label.

        Ignored if time-x mode has been activated with a call to
        L{set_timex}. If called out of context, on the L{Plotter}
        instance, this x-label is used for all subplots and only
        appears in the last (bottom) subplot of each column of
        subplots.
        """
        self.opts['xlabel'] = x
        if not self._isSubplot:
            self._universal_xlabel = True

    def set_ylabel(self, x):
        """
        Sets the y-axis label.
        """
        self.opts['ylabel'] = x

    def set_zeroBottom(self, yes=True):
        """
        Sets the bottom (minimum) of the Y-axis range to zero, unless
        called with C{False}.

        This is useful for plotting values that are never negative and
        where zero is a meaningful absolute minimum.
        """
        self.opts['zeroBottom'] = yes

    def set_zeroLine(self, y=0, color="black", linestyle='--', linewidth=1):
        """
        Adds a horizontal line at the specified I{y} value (default is
        y=0) if the Y-axis range includes that value.

        If y is C{None} or C{False}, clears any previously set line.

        @keyword color: Set the line color (default: black).
        @keyword linestyle: Set the line type (default: '--').
        @keyword linewidth: Set the line width (default: 1).
        """
        self.opts['zeroLine'] = {
            'y': y,
            'color': color,
            'linestyle': linestyle,
            'linewidth': linewidth,
        }

    def use_bump(self, yes=True):
        """
        Bumps up the common y-axis upper limit to 120% of what Matplotlib
        decides. Call with C{False} to disable the bump.
        """
        self.opts['bump'] = yes
        
    def use_grid(self, yes=True):
        """
        Adds a grid, unless called with C{False}.
        """
        self.opts['grid'] = yes

    def use_legend(self, yes=True):
        """
        Has an automatic legend entry added for each plot line, unless
        called with C{False}.
        """
        self.opts['autolegend'] = yes
        
    def use_labels(self, yes=True):
        """
        Has annotation labels point to each plot line instead of a legend,
        with text taken from the legend list. (Works best in
        interactive apps.)

        Call with C{False} to revert to default legend-box behavior.
        """
        self.opts['useLabels'] = yes

    def use_minorTicks(self, axisName=None, yes=True):
        """
        Enables minor ticks for I{axisName} ("x" or "y", omit for
        both). Call with C{False} after the I{axisName} to disable.

        To enable with a specific tick spacing, supply a float instead
        of just C{True}. Or, for a specific number of ticks, supply
        that as an int.

        Note that, due to a Matplotlib limitation, you can't enable
        minor ticks for just one axis, although you can independently
        set the tick spacings.
        """
        if axisName is None:
            for axisName in ('x', 'y'):
                self.use_minorTicks(axisName, yes)
            return
        self._axisOpt('ticks', axisName)['minor'] = yes
        
    def use_timex(self, yes=True):
        """
        Uses intelligent time scaling for the x-axis, unless called with
        C{False}.

        If your x-axis is for time with units in seconds, you can call
        this to have the X values rescaled to the most sensible units,
        e.g., nanoseconds for values < 1E-6. Any I{xlabel} option is
        disregarded in such case because the x label is set
        automatically.
        """
        self.opts['timex'] = yes
        if not self._isSubplot:
            self._universal_xlabel = True

