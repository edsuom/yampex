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

import numpy as np

from yampex.util import sub


class HeightComputer(object):
    """
    I compute vertical (height) spacings for an L{Adjuster} instance I{adj}.

    @keyword universal_xlabel: Set C{True} if all subplots have
        the same xlabel.
    """
    def __init__(self, adj, fHeight, universal_xlabel=False):
        self.adj = adj
        self.sp = adj.sp
        self.fHeight = fHeight
        self.universal_xlabel = universal_xlabel

    def spaceForTitle(self, k):
        """
        Returns the spacing in pixels needed to accommodate the title of
        the subplot at index I{k}.

        The title height is multiplied by 2.0.
        """
        dims = self.adj.getDims(k, 'title')
        return 2*dims[1] if dims else 0

    def spaceForXlabel(self, k):
        """
        Returns the spacing in pixels needed to accommodate the title of
        the subplot at index I{k}.

        The title height is multiplied by 2.0.
        """
        dims = self.adj.getDims(k, 'xlabel')
        return 2*dims[1] if dims else 0
    
    def spaceForTicks(self, k):
        """
        Returns the spacing in pixels needed to accommodate the x-axis
        ticks, including labels, of the subplot at index I{k}.

        The tick+label height is multiplied by 1.5.
        """
        maxTickHeight = 0
        for ytl in self.sp[k].get_xticklabels():
            thisHeight = self.adj.textDims(ytl)[1] * 1.5
            if thisHeight > maxTickHeight:
                maxTickHeight = thisHeight
        return maxTickHeight
    
    def top(self, titleObj=None):
        """
        Returns the spacing in pixels needed to accommodate the top of the
        figure, above all subplots. Supply any figure title
        I{textObj}.

        Unfortunately, the I{textObj} will have some gratuitous space
        above and below it that needs to be accounted for. Scales the
        title height a bit, more so with figure size to make up for
        the extra space above.
        """
        ms = 0
        if titleObj is None:
            titleHeight = 0
        else:
            titleHeight = 1.5*self.adj.textDims(titleObj)[1]
            titleHeight *= 1 + max([0, (self.fHeight-400)/500])
        for k in range(self.sp.N):
            if self.sp.onTop(k):
                s = self.spaceForTitle(k)
                if s: s += 0.65 * titleHeight
                else: s = titleHeight
                if s > ms: ms = s
        #print "TOP", ms
        return ms
    
    def between(self):
        """
        Returns the spacing in pixels needed to accommodate horizontal
        (subplot above and below) gutters between subplots.

        If there's both a title and an xlabel in the subplot above,
        the space for the title is scaled up to leave some whitespace
        between xlabel and title.
        """
        ms = 0
        for k in range(self.sp.N):
            if self.sp.onTop(k): continue
            s = self.spaceForTitle(k)
            kAbove = k - self.sp.Nc
            if kAbove >= 0:
                s_xlabel = self.spaceForXlabel(kAbove)
                if s and s_xlabel: s *= 1.5
                s += s_xlabel
                s += self.spaceForTicks(kAbove)
            if s > ms: ms = s
        #print "BETWEEN", ms
        return ms

    def bottom(self):
        """
        Returns the spacing in pixels needed to accommodate the bottom of
        the figure, below all subplots.
        """
        ms = 0
        for k in range(self.sp.N):
            if self.sp.atBottom(k):
                s = self.spaceForXlabel(k)
                s += self.spaceForTicks(k)
                if s > ms: ms = s
        #print "BOTTOM", ms
        return ms
    

class Adjuster(object):
    """
    I do the hard work of trying to intelligently adjust white space
    around and in between subplots.

    There is definitely some empiricism involved with this, as
    Matplotlib's C{subplots_adjust} command doesn't account for text
    and ticks.
    """
    charWidths = (
        (37,  u"lij|' "),
        (50,  u"![]fI.,:;/\\t"),
        (60,  u"`-(){}r\""),
        (85,  u"*^zcsJkvxy"),
        (95,  u"aebdhnopqug#$L+<>=?_~FZT0123456789"),
        (112, u"BSPEAKVXY&UwNRCHD"),
        (135, u"QGOMm%W@\u22121"))
    
    def __init__(self, p):
        """
        C{Adjuster(p)}
        """
        self.p = p
        self.sp = p.sp
        self.DPI = p.DPI
        self.dims = p.dims

    def textWidth(self, text):
        """
        Returns an estimated width of the supplied I{text} proportional to
        full height. For Arial font.
        
        Adapted from U{https://stackoverflow.com/a/16008023}.
        """
        width = 0 # in millinches
        for s in text:
            for w, chars in self.charWidths:
                if s in chars:
                    width += w
                    break
            else: width += 50
        # Convert to full-height proportion
        return 0.0065 * width
        
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
            text = textObj.get_text()
            # Width
            dims = [size*self.textWidth(text)]
            # Height
            dims.append(size*(0.8+text.count("\n")))
        return dims
        
    def width(self, textObj):
        """
        Returns the width of the supplied text object in pixels.
        """
        return self.textDims(textObj)[0]

    def tickWidth(self, k):
        """
        Returns the maximum width of the y-axis ticks (with labels) for
        subplot I{k}.
        """
        maxTickWidth = 0
        for ytl in self.sp[k].get_yticklabels():
            thisWidth = self.width(ytl)
            if thisWidth > maxTickWidth:
                maxTickWidth = thisWidth
        return maxTickWidth
    
    def getDims(self, k, key):
        """
        Returns the dimensions of the artist referenced with the specified
        I{key} in subplot I{k}, or C{None} if no such artist had its
        dimensions defined for that subplot.
        """
        if k not in self.dims: return
        return self.dims[k].get(key, None)
    
    def wSpace(self, left=False):
        """
        Returns the horizontal (width) space in pixels, to the left of all
        subplots if I{left} is set, or between subplots otherwise.

        @keyword left: Set C{True} to get horizontal space to the left
            of all subplots.
        """
        maxWidth = 0
        for k in range(len(self.sp)):
            if left and not self.sp.onLeft(k):
                continue
            thisWidth = self.tickWidth(k)
            dims = self.getDims(k, 'ylabel')
            if dims:
                # Add twice the ylabel's font height (not width,
                # because rotated 90)
                thisWidth += 2*dims[1]
            if thisWidth > maxWidth:
                maxWidth = thisWidth
        return maxWidth
    
    def scaledWidth(self, x, per_sp=False, scale=1.0, margin=0, pixmin=0):
        pw = self.fWidth
        if per_sp: pw /= self.sp.Nc
        pixels = max([pixmin, x+margin])
        return scale*pixels / pw

    def scaledHeight(self, x, per_sp=False, scale=1.0, margin=0, pmax=0.4):
        ph = self.fHeight
        if per_sp: ph /= self.sp.Nr
        h = scale*(x+margin) / ph
        if pmax and h > pmax: h = pmax
        return h

    def updateFigSize(self, fWidth, fHeight):
        self.fWidth = fWidth
        self.fHeight = fHeight
    
    def __call__(self, universal_xlabel=False, titleObj=0):
        kw = {}
        xlabels = self.p.xlabels
        if universal_xlabel:
            # Thanks to kennytm,
            # https://stackoverflow.com/questions/3844801/
            #  check-if-all-elements-in-a-list-are-identical
            if len(set(xlabels.values())) > 1:
                universal_xlabel = False
        hc = HeightComputer(self, self.fHeight, universal_xlabel)
        for k in xlabels:
            if universal_xlabel and not self.sp.atBottom(k):
                continue
            ax = self.sp.axes[k]
            ax.set_xlabel(xlabels[k])
        kw['top'] = 1.0 - self.scaledHeight(
            hc.top(titleObj), margin=20, pmax=0.14)
        kw['hspace'] = self.scaledHeight(
            hc.between(), per_sp=True, margin=30, pmax=0.4)
        kw['bottom'] = self.scaledHeight(
            hc.bottom(), margin=15, pmax=0.2)
        kw['wspace'] = self.scaledWidth(
            self.wSpace(), per_sp=True, scale=1.3, margin=15, pixmin=55)
        kw['left'] = self.scaledWidth(
            self.wSpace(left=True), scale=1.3, margin=15, pixmin=45)
        return kw
