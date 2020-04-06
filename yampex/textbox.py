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
Text boxes for providing info in plot margins.
"""

import numpy as np

from yampex.adjust import TextSizeComputer
from yampex.util import sub


class TextBoxMaker(object):
    """
    Construct an instance with a Matplotlib C{Axes} object and, to add
    the textbox to a subplot instead of the whole figure, two more
    args: The number of columns and rows in the subplot.

    Any keywords you supply to my constructor are used in the textbox,
    with the exception of I{m}.

    @keyword DPI: The dots per inch of the figure the text box will be
        going into.
    
    @keyword m: The margin between the text box and the edge of the
        figure. If a float, relative to figure or subplot
        dimensions. If an int, in pixels; requires I{fDims} to be
        supplied. (Default: 0.02)

    @keyword fDims: A 2-sequence containing the figure dimensions in
        pixels.
    
    @keyword alpha: The alpha (opacity) of the text box
        background. (Default: 0.8)

    @keyword backgroundcolor: The background color of the text
        box. (Default: white)
    """
    DEBUG = False
    
    _locations = {
        'NE':   1,
        'E':    2,
        'SE':   3,
        'S':    4,
        'SW':   5,
        'W':    6,
        'NW':   7,
        'N':    8,
        'M':    9,
    }
    _XY = {
        1:      (1.0,   1.0),
        2:      (1.0,   0.5),
        3:      (1.0,   0.0),
        4:      (0.5,   0.0),
        5:      (0.0,   0.0),
        6:      (0.0,   0.5),
        7:      (0.0,   1.0),
        8:      (0.5,   1.0),
        9:      (0.5,   0.5),
    }
    _textAlignment = {
        1: ('right',    'top'   ),
        2: ('right',    'center'),
        3: ('right',    'bottom'),
        4: ('center',   'center'),
        5: ('left',     'bottom'),
        6: ('left',     'center'),
        7: ('left',     'top'   ),
        8: ('center',   'center'),
        9: ('center',   'center'),
    }

    kw = {
        'm':                    0.02,
        'fontsize':             10.0,
        'backgroundcolor':      "white",
        # Plots and annotations should be drawn with a higher zorder
        # than 2 (later, i.e., on top of text boxes)
        'zorder':               2,
        'fDims':                None,
    }

    def __init__(self, axOrFig, *args, **kw):
        self.fig = axOrFig.get_figure()
        if self.fig is None:
            self.ax = None
            self.fig = axOrFig
        else: self.ax = axOrFig
        self.NcNr = args
        self.kw = self.kw.copy()
        self.kw.update(kw)
        self.tsc = TextSizeComputer(kw.pop('DPI', None))
        self.t = None

    def conformLocation(self, location):
        if not isinstance(location, int):
            location = self._locations[location.upper()]
        return location

    def get_XY(self, location, dims, margins):
        xy = list(self._XY[location])
        for k, value in enumerate(xy):
            mk = margins[k]*self.NcNr[k] if self.NcNr else margins[k]
            if value == 0.0:
                xy[k] = 0.5*dims[k] + mk
                continue
            if value == 1.0:
                xy[k] = 1.0 - 0.5*dims[k] - mk
        return xy
    
    def __call__(self, location, proto, *args, **options):
        kw = self.kw.copy()
        kw.update(options)
        location = self.conformLocation(location)
        text = sub(proto, *args)
        fDims = kw.pop('fDims')
        margin = kw.pop('m')
        if fDims:
            dims = self.tsc.pixels2fraction(
                self.tsc.dims(text, kw['fontsize']), fDims)
            if isinstance(margin, int):
                margins = [float(margin)/x for x in fDims]
            else: margins = [margin, margin]
        else:
            dims = [0, 0]
            if isinstance(margin, int):
                raise ValueError(
                    "You must supply figure dims with integer margin")
            margins = [margin, margin]
        x, y  = self.get_XY(location, dims, margins)
        kw['horizontalalignment'], kw['verticalalignment'] = \
            self._textAlignment[location]
        if self.ax:
            kw['transform'] = self.ax.transAxes
            obj = self.ax
        else: obj = self.fig
        self.t = obj.text(x, y, text, **kw)
        if self.DEBUG:
            rectprops = {}
            rectprops['facecolor'] = "white"
            rectprops['edgecolor'] = "red"
            self.tList[0].set_bbox(rectprops)
        return self

    def remove(self):
        """
        Removes my text object from the figure, catching the exception
        raised if it's not there.
        """
        if self.t is None: return
        try: self.t.remove()
        except: pass
