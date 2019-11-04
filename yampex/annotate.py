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
Smart plot annotations.
"""

from copy import copy

import numpy as np
import matplotlib.patches as patches

from yampex.adjust import TextSizeComputer
from yampex.util import sub


class Sizer(object):
    """
    I try to provide accurate sizing of annotations.

    Burned up a lot of CPU cycles in the __call__ method, which is
    called many thousands of times. Added use of I{legitDims} list,
    which speeds things up and doesn't seem to incur any problems with
    mis-sizing of evaluation rectangles.
    """
    maxTries = 3
    bogusHeightThreshold = 5 # pixels

    __slots__ = ['dims', 'legitDims']
    
    def __init__(self):
        self.dims = {}
        self.legitDims = []

    def area(self, dims):
        return dims[0] * dims[1]
        
    def __call__(self, ann, tryCount=0):
        text = ann.get_text()
        if text in self.legitDims:
            # Taking a chance that a non-bogus size previously
            # computed can be relied upon. Seems to work, and saves
            # considerable processing time.
            return self.dims[text]
        bb = ann.get_bbox_patch().get_extents()
        theseDims = (bb.width, bb.height)
        if theseDims[1] < self.bogusHeightThreshold and \
           tryCount < self.maxTries:
            ann.draw(ann.axes.figure.canvas.get_renderer())
            return self(ann, tryCount+1)
        prevDims = self.dims.get(text, (0,0))
        if self.area(theseDims) > self.area(prevDims):
            self.dims[text] = theseDims
            self.legitDims.append(text)
        return self.dims[text]


class RectangleRegion(object):
    """
    I am a rectangular plot region where an annotation is or might go.
    """
    def __init__(self, ann, relpos, x01, y01):
        self.ann = ann
        self.relpos = relpos
        self.xy = ann.axes.transData.transform(ann.xy)
        self.x0, self.x1 = x01
        self.y0, self.y1 = y01

    def __repr__(self):
        args = list(self.ann.xy)
        for x in self.xy[0], self.xy[1], self.x0, self.y0, self.x1, self.y1:
            args.append(int(round(x)))
        return sub(
            "({:.0f}, {:.0f}): ({:d}, {:d}) --> [{:d},{:d} {:d},{:d}]", *args)

    def patch(self, color):
        """
        Returns a Matplotlib patch object representing me. It will be
        drawn as an unfilled rectangle of the specified I{color}.
        """
        return patches.Rectangle(
            [self.x0, self.y0], self.x1-self.x0, self.y1-self.y0,
            color=color, fill=False)
    
    def xOverlap(self, other):
        if self.x1 < other.x0:
            # My annotation is fully to the left of this one
            return False
        if self.x0 > other.x1:
            # Mine is fully to the right of it
            return False
        return True
        
    def yOverlap(self, other):
        if self.y1 < other.y0:
            # My annotation is fully below this one
            return False
        if self.y0 > other.y1:
            # Mine is fully above it
            return False
        return True
    
    def overlap(self, other):
        return self.xOverlap(other) and self.yOverlap(other)

    def arrowOverlap(self, other):
        def zBetweenAB(a, b, z):
            """Is z between a and b? (Make sure a < b)"""
            return z > a and z < b

        x, y = self.xy
        if self.relpos[0] == 0.5:
            # Vertical arrow
            if x < other.x0 or x > other.x1:
                return False
            # Arrow between other's vertical sides
            if self.y1 < other.y0:
                # Other is above me...
                if y < self.y0 or zBetweenAB(self.y1, other.y0, y):
                    # ...so no overlap if arrow points down or is
                    # between us
                    return False
            elif y > self.y1 or zBetweenAB(other.y1, self.y0, y):
                # Other is below me, so no overlap if arrow points up
                # or is in between us
                return False
            # There must be overlap
            return True
        if self.relpos[1] == 0.5:
            # Horizontal arrow
            if y < other.y0 or y > other.y1:
                return False
            # Arrow between other's horizontal sides
            if self.x1 < other.x0:
                # Other is to my right...
                if x < self.x0 or zBetweenAB(self.x1, other.x0, x):
                    # ...so no overlap if arrow points to the left or
                    # is between us
                    return False
            elif x > self.x1 or zBetweenAB(other.x1, self.x0, x):
                # Other is to my left, so no overlap if arrow points
                # to the right or is in between us
                return False
            # There must be overlap
            return True
        # TODO: Angled arrow, not (yet) tested
        return False


class Positioner(object):
    """
    I take care of positioning an annotation. 
    
    All data is saved and computations done in pixel units. 
    """
    colors = [
        'black', 'brown', 'red', 'orange',
        'yellow', 'green', 'blue', 'violet']
    
    relpos = [
        (0.0, 0.0),     # NE
        (0.0, 0.5),     # E
        (0.0, 1.0),     # SE
        (0.5, 1.0),     # S
        (1.0, 1.0),     # SW
        (1.0, 0.5),     # W
        (1.0, 0.0),     # NW
        (0.5, 0.0),     # N
    ]
    rectanglePadding = 0 #2
    # I hate fudge factors, but rectangle analysis region is shifted
    # too far without this
    ffShift = 0 #5
    # Show warnings and trial position rectangles
    verbose = False
    
    def __init__(self, sizer, axList, pairs):
        self.annotations = {}
        self.sizer = sizer
        self.axList = axList
        self.xyLists = {}
        self.pairs = pairs
        #self.prevData(pairs)

    @property
    def relpos(self):
        if not getattr(self, 'r', None):
            return
        return self.r.relpos

    def __iter__(self):
        for ann, r in self.annotations.copy().itervalues():
            if self.key(ann) in self.annotations:
                yield ann

    def key(self, ann):
        """
        Returns a unique integer key based on the supplied annotation
        object's non-transformed (original) x,y coordinates and which
        axis it belongs to.
        """
        return hash((ann.axes, ann.xy))
                
    def add(self, ann, r=None):
        """
        Adds a record for the supplied annotation object I{ann},
        sub-categorized by the axis I{ax} it belongs to.

        Unless a rectangle object is also supplied, cleanly
        replaces any annotation that already exists for that axis with
        the same non-transformed x,y coordinates, deleting all
        rectangle objects from the record.

        If a rectangle object is supplied with the I{r} keyword, adds
        it to the list associated with the supplied annotation in the
        record.

        If my I{verbose} attribute is C{True}, adds an unfilled
        colored rectangle to the figure for annotation position
        debugging purposes. The colors follow the resistor color code,
        with the first attempted position being drawn in black, the
        second being brown, etc.
        """
        key = self.key(ann)
        if r is None:
            if key in self.annotations:
                self.remove(ann)
        elif key in self.annotations:
            rList = self.annotations[key][1]
            rList.append(r)
            if self.verbose:
                k = len(rList) % len(self.colors)
                patch = r.patch(self.colors[k])
                ann.axes.get_figure().patches.append(patch)
            return
        self.annotations[key] = (ann, [])
            
    def remove(self, ann, ax=None):
        """
        Removes the record for the supplied annotation object I{ann}.

        If an Axes object is found, removes all rectangle patches
        present in the Figure for the Axes. If an Axes object is also
        supplied via the keyword I{ax}, uses that instead of looking
        for one as an I{axes} attribute of the annotation object.
        """
        key = self.key(ann)
        if ax is None: ax = ann.axes
        fig = None if ax is None else ax.get_figure()
        if key in self.annotations:
            null, rList = self.annotations.pop(key)
        else: rList = []
        if fig is None: return
        for r in rList:
            if r in fig.patches: fig.patches.remove(r)
    
    def dataToPixels(self, ann=None, kAxes=None, ax=None, xyData=None):
        """
        Returns...
        """
        if ax is None:
            ax = self.axList[kAxes] if ann is None else ann.axes
        if xyData is None:
            if kAxes is None:
                xy = ann.xy
            else:
                xy = np.column_stack(self.pairs.getXY(kAxes))
        else: xy = xyData
        if isinstance(xy, list) and len(xy) == len(self.axList)+1:
            xy2 = []
            if kAxes is None: kAxes = self.axList.index(ax)
            for k in range(len(xy[0])):
                xy2.append([xy[0][k], xy[kAxes][k]])
            xy = xy2
        try:
            XY = ax.transData.transform(xy)
        except:
            if self.verbose:
                print(sub(
                    "WARNING: Couldn't transform xy:\n{}...\n",
                    repr(xy)[:300]))
            return
        if len(XY.shape) > 1:
            return [XY[:,k] for k in (0,1)]
        return XY
                
    def rectangle(self, ann, dx, dy):
        """
        Sets up a new overlap analysis with the supplied annotation and
        proposed x and y offset (pixel units) from its current location.

        The offset is adjusted so that positive x or y offset puts the
        left or lower corner at that point, negative x or y offset
        puts the right or upper corner there, and zero x or y offset
        puts the middle of the edge there.

        Returns a L{RectangleRegion} with the four points
        """
        def shift(x_y, dx_y, dim):
            if dx_y < 0:
                relpos.append(1.0)
                x_y1 = x_y + dx_y + self.ffShift
                x_y0 = x_y1 - dim
            elif dx_y > 0:
                relpos.append(0.0)
                x_y0 = x_y + dx_y - self.ffShift
                x_y1 = x_y0 + dim
            else:
                relpos.append(0.5)
                x_y0 = x_y - 0.5*dim
                x_y1 = x_y + 0.5*dim
            return x_y0 - self.rectanglePadding, x_y1 + self.rectanglePadding
        
        relpos = []
        xy = self.dataToPixels(ann=ann)
        if xy is None: return
        width, height = self.sizer(ann)
        x01 = shift(xy[0], dx, width)
        y01 = shift(xy[1], dy, height)
        print "P-R", self, ann.xy, relpos, x01, y01
        r = RectangleRegion(ann, relpos, x01, y01)
        return r
    
    def liveData(self, kAxes, *xy):
        xyLists = self.xyLists.setdefault(kAxes, [[], []])
        if xy:
            x, y = xy
            k = np.searchsorted(xyLists[0], x)
            xyLists[0].insert(k, x)
            xyLists[1].insert(k, y)
        return np.column_stack(xyLists)

    def prevData(self, pairs=None):
        if pairs is None:
            return getattr(self, '_prevData', None)
        self._prevData = pairs.copy()
    
    def datarator(self):
        """
        Yields X and Y transformed to pixels with current axes display
        """
        N = len(self.axList)
        for kAxes in range(N):
            yield self.dataToPixels(kAxes=kAxes)
            xyData = self.liveData(kAxes)
            if xyData.shape[0]:
                yield self.dataToPixels(kAxes=kAxes, xyData=xyData)
        # Why needed?
        #xyData = self.prevData()
        #if xyData is not None:
        #    yield self.dataToPixels(kAxes=kAxes, xyData=xyData)
    
    def with_data(self, ann, r):
        """
        Returns score for overlapping with X,Y data for all
        axes. Increases with number of plot lines overlapped.
        """
        def sliceSpanningRectangle():
            k0 = np.searchsorted(X, r.x0)
            k1 = np.searchsorted(X, r.x1) + 1
            return slice(k0, k1)
        
        s = None
        score = 0.0
        for XY in self.datarator():
            if XY is None:
                continue
            X, Y = XY
            # Get slice of Y spanning same X interval as annotation
            newX = False
            if s is None:
                # First data set
                Xmm = X.min(), X.max()
                s = sliceSpanningRectangle()
            else:
                thisXmm = X.min(), X.max()
                if thisXmm != Xmm:
                    # Data set with different X interval from the
                    # previous one
                    Xmm = thisXmm
                    s = sliceSpanningRectangle()
            if r and np.all(np.less(Y[s], r.y0)):
                continue
            if r and np.all(np.greater(Y[s], r.y1)):
                continue
            score += 1.5
            if score >= self.mustBeat: break
        return score

    def with_boundary(self, ann, r):
        """
        Returns score for overlapping with (or going beyond) axis
        boundary, and twice as bad a score for such a conflict with
        the figure boundary.
        """
        score = 0.0
        ax = ann.axes
        for k, obj in enumerate((ax, ax.figure)):
            points = obj.get_window_extent().get_points()
            x0, y0 = points[0]
            x1, y1 = points[1]
            if r.x0 < x0 or \
               r.x1 > x1 or \
               r.y0 < y0 or \
               r.y1 > y1:
                score += 3*(k+1)
            else:
                return score
        return score

    def with_others(self, ann, r):
        """
        Returns score for overlapping with any other annotation.
        """
        score = 0.0
        for other in self:
            if other is ann:
                continue
            tr = self.rectangle(other, *other.xyann)
            if tr is None: continue
            if r and r.overlap(tr):
                return 4.0
            # Return somewhat less bad score if there is arrow overlap
            if r and r.arrowOverlap(tr):
                score += 2.0
            # TODO: Account for angled arrows, too
            if score >= self.mustBeat:
                break
        return score
    
    def __call__(self, ann, offset, radius, mustBeat=1E9):
        """
        Sets up a new overlap analysis with the supplied annotation and
        proposed x and y offset (pixel units) from its current location.
        """
        fig = ann.axes.get_figure()
        r = self.rectangle(ann, *[radius*x for x in offset])
        self.add(ann, r)
        self.mustBeat = mustBeat
        score = self.with_boundary(ann, r)
        if score < mustBeat:
            score += self.with_others(ann, r)
        if score < mustBeat:
            score += self.with_data(ann, r)
        return radius*score


class Annotator(object):
    """
    I manage the annotations for all axes in a subplot. Construct me
    with a list of the axes and call the instance to add each new
    annotation.
    """
    rp = 28.3
    offsets = [
        (+20, +20),     # NE
        (+rp,   0),     # E
        (+20, -20),     # SE
        (  0, -rp),     # S
        (-20, -20),     # SW
        (-rp,   0),     # W
        (-20, +20),     # NW
        (  0, +rp),     # N
    ]
    moreOffsets = [
        (+11, +26),     # NNE
        (+26, +11),     # ENE
        (+26, -11),     # ESE
        (+11, -26),     # SSE
        (-11, -26),     # SSW
        (-26, -11),     # WSW
        (-26, +11),     # WNW
        (-11, +26),     # NNW
    ]
    radii = [1.0, 2.0, 4.0, 8.0, 12.0, 16.0]

    fontsize = 12 # points
    # Estimated mapping of string fontsizes to points
    fontsizeMap = TextSizeComputer.fontsizeMap
    fontWeight = 'normal'
    arrowprops = {
        'facecolor':            "#800000",
        'edgecolor':            "#800000",
        'arrowstyle':           "-|>",
        'connectionstyle':      "arc3",
        'relpos':               (0.5, 0.5),
    }
    _boxprops = {
        # boxstyle is set in constructor based on fontsize
        #'boxstyle':             "round,pad=0.15",
        'facecolor':            "white",
        'edgecolor':            "#800000",
        'lw':                   2,
        'alpha':                0.8,
    }
    maxDepth = 10

    # PROFILE
    #from cProfile import Profile
    #P = Profile()

    @classmethod
    def setVerbose(cls, yes=True):
        Positioner.verbose = yes
    
    def __init__(self, axList, pairs, **kw):
        self.axList = axList
        self.sizer = Sizer()
        self.p = Positioner(self.sizer, axList, pairs)
        for name in kw:
            setattr(self, name, kw[name])
        self.boxprops = self._boxprops.copy()
        self.boxprops['boxstyle'] = sub(
            "round,pad={:0.3f}", self.paddingForSize())

    def paddingForSize(self):
        fs = self.fontsize
        if fs in self.fontsizeMap:
            fs = self.fontsizeMap[fs]
        return min([0.25, 0.44 - 0.008*fs])
    
    def offseterator(self, radius):
        for k, offsets in enumerate(self.offsets):
            yield offsets
            if radius > 2:
                yield self.moreOffsets[k]
        
    def scaledOffset(self, radius, offset):
        return [radius*x for x in offset]
        
    def textAlignment(self, relpos):
        if relpos[0] == 0:
            ha = "left"
        elif relpos[0] == 1:
            ha = "right"
        else:
            ha = "center"
        if relpos[1] == 0:
            va = "bottom"
        elif relpos[1] == 1:
            va = "top"
        else:
            va = "center"
        return ha, va

    def evaluate(self, ann, depth=0):
        def setBest():
            best['score'] = score
            best['offset'] = self.scaledOffset(radius, offset)
            best['relpos'] = self.p.relpos

        def realDifference(a, b):
            for k in (0, 1):
                if abs(a[k] - b[k]) > 0.5: return True
            return False

        def radiusPenalty(radius):
            if radius > 2:
                return 0.2*np.sqrt(radius)
            return 0

        best = {'score': 1E9}
        for k, radius in enumerate(self.radii):
            for offset in self.offseterator(radius):
                score = self.p(ann, offset, radius, mustBeat=best['score'])
                if score < best['score']: setBest()
                if score == 0: break
            if best['score'] == 0: break
            best['score'] += radiusPenalty(radius)
            if k+1 < len(self.radii):
                nextRadius = self.radii[k+1]
                if best['score'] < radiusPenalty(nextRadius):
                    # Even a clear spot would be scored worse at next
                    # higher radius, so we're done
                    break
            
        offset = best['offset']
        if realDifference(offset, ann.xyann):
            return self.replace(
                ann, offset=offset, relpos=best['relpos'], depth=depth)
        return ann
    
    def update(self, *args, **kw):
        depth = kw.pop('depth', 0) + 1
        if depth > self.maxDepth:
            return False
        updated = False
        for ann in self.p:
            result = self.evaluate(ann, depth)
            if result != ann:
                updated = True
        return updated
    
    def add(self, ax, text, xy, offset=None, relpos=None, depth=0):
        if offset is None: offset = (0,0)
        arrowprops = self.arrowprops.copy()
        if relpos:
            arrowprops['relpos'] = relpos
            ha, va = self.textAlignment(relpos)
        else:
            ha, va = ['center']*2
        ann = ax.annotate(
            text, xy=xy, xytext=offset,
            textcoords="offset pixels",
            ha=ha, va=va, size=self.fontsize, weight=self.fontWeight,
            arrowprops=arrowprops, bbox=self.boxprops, zorder=100)
        self.p.add(ann)
        ann.draw(ax.figure.canvas.get_renderer())
        # PROFILE
        # ---------------------------------------------
        #self.P.runcall(self.update, depth=depth)
        self.update(depth=depth)
        # ---------------------------------------------
        return ann

    def remove(self, ann, ax=None):
        if ax is None: ax = ann.axes
        for thisAnn in ax.findobj(match=type(ann)):
            if thisAnn.get_text() == ann.get_text():
                thisAnn.remove()
                self.p.remove(thisAnn, ax)
        self.p.remove(ann, ax)
    
    def replace(self, ann, **kw):
        # Doesn't the annotation always have an .axes attribute?
        ax = kw.get('ax', None)
        if ax is None: ax = ann.axes
        xy = kw.get('xy', None)
        if xy is None: xy = ann.xy
        text = kw.get('text', None)
        if text is None: text = ann.get_text()
        self.remove(ann, ax)
        return self.add(
            ax, text, xy,
            kw.get('offset', None), kw.get('relpos', None), kw.get('depth', 0))
    
    def __call__(self, kAxis, x, y, text):
        ax = self.axList[kAxis]
        ann = self.add(ax, text, (x, y))
        return ann


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
    }

    kw = {
        'm':                    0.02,
        'fontsize':             10.0,
        'alpha':                1.0,
        'backgroundcolor':      "white",
        'zorder':               5,
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
            self.t = self.ax.text(x, y, text, **kw)
        else: self.t = self.fig.text(x, y, text, **kw)
        if self.DEBUG:
            self.t.set_bbox({'facecolor': "white", 'edgecolor': "red"})
        return self

    def remove(self):
        """
        Removes my text object from the figure, catching the exception
        raised if it's not there.
        """
        try:
            self.t.remove()
        except: pass
