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


class Adjuster(object):
    """
    I do the hard work of trying to intelligently adjust white space
    around and in between subplots.

    There is definitely some empiricism involved with this, as
    Matplotlib's C{subplots_adjust} command doesn't account for text
    and ticks.
    """
    def __init__(self, p):
        self.p = p
        self.sp = p.sp
        self.DPI = p.DPI
        self.dims = p.dims

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
            dims = [0.4*size*len(text)]
            # Height
            dims.append(size*(1+text.count("\n")))
        return dims
        
    def width(self, x):
        return self.textDims(x)[0]

    def height(self, x):
        return self.textDims(x)[1] * 1.5
    
    def tickWidth(self, k):
        maxTickWidth = 0
        for ytl in self.sp[k].get_yticklabels():
            thisWidth = self.width(ytl)
            if thisWidth > maxTickWidth:
                maxTickWidth = thisWidth
        return maxTickWidth
    
    def tickHeight(self, k):
        maxTickHeight = 0
        for ytl in self.sp[k].get_yticklabels():
            thisHeight = self.height(ytl)
            if thisHeight > maxTickHeight:
                maxTickHeight = thisHeight
        return maxTickHeight

    def getDims(self, k, key):
        if k not in self.dims: return
        return self.dims[k].get(key, None)
    
    def wSpace(self, left=False):
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
    
    def hSpace(self, top=False, bottom=False, universal_xlabel=False):
        maxHeight = 0
        for k in range(len(self.sp)):
            if top and not self.sp.onTop(k):
                continue
            if bottom and not self.sp.atBottom(k):
                continue
            thisHeight = 0
            if not top:
                # Ticks
                thisHeight += self.tickHeight(k)
                # Subplot xlabel, if shown for this row
                if bottom or not universal_xlabel or self.sp.atBottom():
                    dims = self.getDims(k, 'xlabel')
                    if dims:
                        # Add twice the xlabel's font height
                        thisHeight += 2*dims[1]
            # Subplot title
            if not bottom:
                dims = self.getDims(k, 'title')
                if dims:
                    # Add twice the title's font height
                    thisHeight += 2*dims[1]
            if thisHeight > maxHeight:
                maxHeight = thisHeight
        return maxHeight

    def scaledWidth(self, x, per_sp=False, scale=1.0, margin=30):
        pw = self.fWidth
        if per_sp: pw /= self.sp.Nc
        return scale*(x+margin) / pw

    def scaledHeight(self, x, per_sp=False, scale=1.0, margin=30, limit=0.3):
        ph = self.fHeight
        if per_sp: ph /= self.sp.Nr
        h = scale*(x+margin) / ph
        if limit and h > limit: h = limit
        return h

    def updateFigSize(self, fWidth, fHeight):
        self.fWidth = fWidth
        self.fHeight = fHeight
    
    def __call__(self, xlabels, universal_xlabel=False, titleHeight=0):
        kw = {}
        if universal_xlabel:
            # Thanks to kennytm,
            # https://stackoverflow.com/questions/3844801/
            #  check-if-all-elements-in-a-list-are-identical
            if len(set(xlabels.values())) > 1:
                universal_xlabel = False
        textObj = None
        for k in xlabels:
            if universal_xlabel and not self.sp.atBottom(k):
                continue
            ax = self.sp.axes[k]
            ax.set_xlabel(xlabels[k])
        top_pixels = self.hSpace(top=True)
        if top_pixels: titleHeight *= 0.6
        top_pixels += titleHeight
        kw['top'] = 1.0 - self.scaledHeight(top_pixels, margin=15, limit=0.15)
        kw['hspace'] = self.scaledHeight(
            self.hSpace(universal_xlabel=universal_xlabel), per_sp=True)
        kw['bottom'] = self.scaledHeight(self.hSpace(bottom=True), margin=15)
        kw['wspace'] = self.scaledWidth(
            self.wSpace(), per_sp=True, scale=1.3, margin=15)
        kw['left'] = self.scaledWidth(
            self.wSpace(left=True), scale=1.3, margin=15)
        return kw
