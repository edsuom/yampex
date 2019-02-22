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
The L{Plotter} methods defined by its L{OptsBase} base class give
you a convenient API for setting tons of options for the next subplot.

Or, if you call your C{Plotter} instance outside the subplot in
context (before the C{with...as} statement), calling these methods
defines options for all subplots.

Keep the API for L{OptsBase} handy, and maybe a copy of the
U{source<http://edsuom.com/yampex/yampex.options.py>} open in your
editor, as a handy reference for all the plotting options you can set.
"""

from copy import copy

from yampex.util import sub


class Opts(dict):
    """
    I am a dict-like object of options, making a deep copy of the dict
    you supply to my constructor and providing a few other useful
    methods.
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

    def __init__(self, other={}):
        dict.__init__(self)
        for key in self._opts:
            value = other[key] if key in other else self._opts[key]
            dict.__setitem__(self, key, copy(value))

    def deepcopy(self):
        """
        Returns a deep copy of me, with copies of all my items as they
        exist right now.
        """
        return Opts(self)

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

    def kwModified(self, k, kw_orig, **moreOpts):
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
        for key in moreOpts:
            if nd(key):
                kw[key] = moreOpts[key]
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
        """
        self.opts['error'] = yes
        
    def set_useLabels(self, yes=True):
        """
        Has annotation labels point to each plot line instead of a legend,
        with text taken from the legend list.

        Call with C{False} to revert to default legend-box behavior.
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
        Bumps up the common y-axis upper limit.
        
        If you don't manually set a yscale with a call to
        L{set_yscale}, you can call this method to increase the common
        y-axis upper limit to 120% of what Matplotlib decides. Call
        with C{False} to disable the bump.
        """
        self.opts['bump'] = yes

    def set_zeroBottom(self, yes=True):
        """
        Sets the bottom (minimum) of the Y-axis range to zero, unless
        called with C{False}.

        This is useful for plotting values that are never negative and
        where zero is a meaningful absolute minimum.
        """
        self.opts['zeroBottom'] = yes

    def set_zeroLine(self, y=0):
        """
        Adds a horizontal line at the specified I{y} value (default is
        y=0) if the Y-axis range includes that value.

        If y is C{None} or C{False}, clears any previously set line.
        """
        self.opts['zeroLine'] = y
        
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

    def add_line(self, x=None, width=None):
        """
        Appends the supplied line style character to the list of line
        styles being used.

        The first and possibly only line style in the list applies to
        the first vector plotted within a given subplot. If there is
        an additional vector being plotted within a given subplot
        (three or more arguments supplied when calling the L{Plotter}
        object, and more than one line style has been added to the
        list, then the second line style in the list is used for that
        second vector plot line. Otherwise, the first (only) line
        style in the list is used for the second plot line as well.

        You can specify a I{width} for the line as well.
        
        If no line style character or C{None} is supplied, clears the
        list of line styles.
        """
        if x is None:
            self.opts['linestyles'] = []
            return
        self.opts['linestyles'].append((x, width))

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
        
    def set_yscale(self, x=True):
        """
        Rescales the plotted height of all vectors after the first
        dependent one to be plotted, relative to that first dependent
        one, by setting a y scale for it.

        The result is two different twinned x-axes (one for the first
        dependent vector and one for everybody else) and a different
        y-axis label on the right.

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

    def set_minorTicks(self, axisName, yes=True):
        """
        Enables minor ticks for I{axisName} ("x" or "y").
        """
        self._axisOpt('ticks', axisName)['minor'] = yes
        
    def set_axvline(self, k):
        """
        Adds a vertical dashed line at the data point with integer index
        I{k}.

        To set it to an x value, use a float for I{k}.
        """
        self.opts['axvlines'].append(k)
        
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

    def add_legend(self, proto, *args):
        """
        Adds the supplied format-substituted text to the list of legend
        entries.

        You may include a text I{proto}type with format-substitution
        I{args}, or just supply the final text string with no further
        arguments.
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
        Sets the list of legend entries.

        Supply a list of legend entries, either as a single argument
        or with one entry per argument. You can set the I{fontsize}
        keyword to the desired fontsize of the legend; the default is
        'small'.
        """
        if len(args) == 1 and hasattr(args[0], '__iter__'):
            args = args[0]
        self.opts['legend'] = list(args)
        if 'fontsize' in kw:
            self.opts['fontsizes']['legend'] = kw['fontsize']
    
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
        Adds a text box to the specified I{quadrant} of the subplot.

        Quadrants are "NW", "NE", "SE", and "SW". If there's already a
        text box there, a line will be added to it.

        You may include a text I{proto}type with format-substitution
        I{args}, or just supply the final text string with no further
        arguments.
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
        just the present subplot (if called in context).

        You may include a text I{proto}type with format-substitution
        I{args}, or just supply the final text string with no further
        arguments.
        """
        text = sub(proto, *args)
        if self._isSubplot:
            self.opts['title'] = text
        else: self._figTitle = text

    def set_fontsize(self, name, fontsize):
        """
        Sets the I{fontsize} of the specified artist I{name}.

        Recognized names are 'legend' and 'annotations'.
        """
        self.opts['fontsizes'][name] = fontsize
