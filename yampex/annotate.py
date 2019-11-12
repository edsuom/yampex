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


def getOffset(ann):
    """
    Returns the offset of the supplied Matplotlib annotation object,
    in pixels from its data point location on its subplot.

    OR IS IT ABSOLUTE????
    """
    return ann.get_position()


class Sizer(object):
    """
    I try to provide accurate sizing of annotations. Call my instance
    with a Matplotlib annotation object to get an estimate of its
    dimensions in pixels.

    Burned up a lot of CPU cycles in the L{__call__} method, which is
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

    Construct me with the annotation I{ann}, the number of pixels to
    the right I{dx} and up I{dy} from that annotation's data-point
    location to the center of the proposed location, the I{width}, and
    the I{height}.

    The positioning of the region is like so, with "A" being the
    annotation's data-point location, "C" being the center of my
    rectangular region::

                      |
                      |         +------------------+ y1   ^
                      |         |                  |      :
                      ^ ....... |....... C         |   height
                      :         |        .         |      :
                      :         +------------------+ y0   V
                      dy       x0        .         x1
                      :         <=== width ========>
                      :                  .
                      V                  .
        --------------A<=== dx ==========>------------------------------------
                      |
                      |
    """
    def __init__(self, ann, dx, dy, width, height):
        self.ann = ann
        Ax, Ay = self._annXY()
        Cx = Ax + dx
        Cy = Ay + dy
        self.x0 = Cx - 0.5*width
        self.x1 = Cx + 0.5*width
        self.y0 = Cy - 0.5*height
        self.y1 = Cy + 0.5*height

    def __repr__(self):
        args = [int(round(x)) for x in self._annXY()]
        for x in self.x0, self.y0, self.x1, self.y1:
            args.append(int(round(x)))
        return sub("({:d}, {:d}) --> [{:d},{:d} {:d},{:d}]", *args)

    def _annXY(self, ann=None):
        """
        Returns my annotation object's data point coordinates, in pixels.
        """
        try:
            Ax, Ay = self.ann.axes.transData.transform(self.ann.xy)
        except:
            import pdb; pdb.set_trace()
        return Ax, Ay
            
    def _xOverlap(self, other):
        if self.x1 < other.x0:
            # I am fully to the left of the other
            return False
        if self.x0 > other.x1:
            # I am fully to the right of it
            return False
        return True
        
    def _yOverlap(self, other):
        if self.y1 < other.y0:
            # I am fully below the other
            return False
        if self.y0 > other.y1:
            # I am fully above it
            return False
        return True

    def overlaps_datapoint(self):
        """
        Returns C{True} if I overlap my annotation's data point and thus
        its arrow.
        """
        Ax, Ay = self._annXY()
        if self.x0 < Ax and self.x1 > Ax:
            return True
        if self.y0 < Ay and self.y1 > Ay:
            return True
    
    def overlaps_other(self, other):
        """
        Returns C{True} if I overlap the I{other} L{RectangleRegion}
        instance.
        """
        return self._xOverlap(other) and self._yOverlap(other)

    def overlaps_arrow(self, other):
        """
        Returns C{True} if my arrow overlaps the I{other}
        L{RectangleRegion} instance.

        B{TODO}: Make this work, deal with relpos.
        """
        def zBetweenAB(a, b, z):
            """Is z between a and b? (Make sure a < b)"""
            return z > a and z < b

        x, y = self._annXY()
        if self.relpos[0] == 0.5:
            # Vertical arrow
            if x < other.x0 or x > other.x1:
                # No overlap because arrow is entirely to the left or
                # right of the other
                return False
            # Arrow between other's vertical sides
            if self.y1 < other.y0:
                # Other is above me...
                if y < self.y0 or zBetweenAB(self.y1, other.y0, y):
                    # ...so no overlap because arrow points down or is
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


class PositionEvaluator(object):
    """
    Use an instance of me to evaluate the overlap score of a proposed
    position of an annotation, based on subplot data, boundaries, and
    the positions of all other annotations in the subplot.
    
    All subplot data is converted to, and computations done in, pixel
    units.
    """
    rectanglePadding = 0 #2
    # I hate fudge factors, but rectangle analysis region is shifted
    # too far without this
    ffShift = 0 #5
    # Show warnings and trial position rectangles
    verbose = False
    
    def __init__(self, ax, pairs, annotations):
        self.ax = ax
        self.pairs = pairs
        self.annotations = annotations
        self.sizer = Sizer()

    def with_data(self, ann, rr):
        """
        Returns score for the proposed I{RectangleRegion} I{rr} of the
        annotation I{ann} overlapping with X,Y data.

        The score increases with the number of plot lines overlapped.
        """
        def sliceSpanningRectangle():
            k0 = np.searchsorted(X, rr.x0) - 1
            k1 = np.searchsorted(X, rr.x1) + 1
            return slice(k0, k1)
        
        s = None
        score = 0.0
        for pair in self.pairs:
            XY = pair.getXY(asArray=True)
            XY = ann.axes.transData.transform(XY)
            X = XY[:,0]; Y = XY[:,1]
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
            if np.all(np.less(Y[s], rr.y0)):
                # All data points below rectangle region
                continue
            if np.all(np.greater(Y[s], rr.y1)):
                # All data points above rectangle region
                continue
            score += 1.5
            if score >= self.awful:
                # It's as bad as it's meaningfully going to get, no
                # point looking any further
                break
        return score

    def with_boundary(self, ann, rr):
        """
        Returns score for the proposed I{RectangleRegion} I{rr} of the
        annotation I{ann} overlapping with (or going beyond) axis or
        figure boundary.

        The score is twice as high for an overlap with the figure
        boundary.
        """
        score = 0.0
        ax = ann.axes
        for k, obj in enumerate((ax, ax.figure)):
            points = obj.get_window_extent().get_points()
            x0, y0 = points[0]
            x1, y1 = points[1]
            if rr.x0 < x0 or \
               rr.x1 > x1 or \
               rr.y0 < y0 or \
               rr.y1 > y1:
                score += 3*(k+1)
            else:
                return score
        return score
    
    def with_others(self, ann, rr):
        """
        Returns score for the proposed I{RectangleRegion} I{rr} of the
        annotation I{ann} overlapping with any other annotation.

        The score increases with the number of overlaps.
        """
        score = 0.0
        for ann_other in self.annotations:
            if ann_other is ann:
                # This one is the same as the supplied annotation, so
                # ignore it
                continue
            dx, dy = getOffset(ann_other)
            width, height = self.sizer(ann_other)
            rr_other = RectangleRegion(ann_other, dx, dy, width, height)
            if rr.overlaps_other(rr_other):
                return 4.0
            # Return somewhat less bad score if there is arrow overlap (TODO)
            if False and rr.overlaps_arrow(rr_other):
                score += 2.0
            # TODO: Account for angled arrows, too
            if score >= self.awful:
                break
        return score
    
    def score(self, ann, dx, dy, awful=1E9):
        """
        Computes the total overlap score for the annotation if it were
        positioned in my subplot at the specified offset I{dx} and
        I{dy} in pixels from its data point.

        A higher overlap score is worse. A zero overlap score (best
        case) indicates no overlap with anything else at that
        offset. A score of I{awful} is considered as bad as it gets,
        and there's no point in differentiating between it and
        anything worse.

        Returns a 2-tuple with the overlap score and the
        L{RectangleRegion} object I construct for its proposed
        location in my subplot.
        """
        fig = ann.axes.get_figure()
        width, height = self.sizer(ann)
        rr = RectangleRegion(ann, dx, dy, width, height)
        if rr.overlaps_datapoint():
            return awful, rr
        self.awful = awful
        score = self.with_boundary(ann, rr)
        if score < awful:
            score += self.with_others(ann, rr)
        if score < awful:
            score += self.with_data(ann, rr)
        return score, rr


class DebugBoxer(object):
    """
    I draw a colored box at to visually represent L{RectangleRegion}
    instances for debugging purposes.

    The boxes are unfilled rectangles with colors following the
    resistor color code indexed from 1, with the first attempted
    position being drawn in brown (#1), the second being red (#2),
    etc.
    """
    colors = ['brown', 'red', 'orange', 'yellow', 'green', 'blue', 'violet']

    def __init__(self, fig):
        self.fig = fig
        self.k = 0
    
    def add(self, rr):
        """
        Adds a debugging box to my figure at the position of the supplied
        L{RectangleRegion} object I{rr}.
        """
        self.k = (self.k + 1) % len(self.colors)
        patch = patches.Rectangle(
            [rr.x0, rr.y0], rr.x1-rr.x0, rr.y1-rr.y0,
            color=self.colors[self.k], fill=False)
        self.fig.patches.append(patch)
    
    
class Annotator(object):
    """
    I manage the annotations for all axes in a single subplot. You'll
    need an instance of me for each subplot that contains annotations.

    Construct me with the Matplotlib C{Axes} object for my subplot and
    a L{PlotHelper.Pairs} instance that holds L{PlotHelper.Pair}
    objects representing the info for one X, Y pair of vectors to be
    plotted. Call L{add} on the instance to add each new annotation,
    and L{update} to intelligently (re)position the annotations to
    avoid overlap with subplot borders, plot data, and other
    annotations.

    @ivar sizer: An instance of L{Sizer} for estimating dimensions of
        Matplotlib annotation objects.
    
    @ivar pos: An instance of L{PositionEvaluator} that uses my
        I{sizer} instance.

    @ivar annotations: A list of all Matplotlib annotation objects in
        my subplot. A reference is passed to the constructor of
        L{Sizer} and used by it as well.

    @ivar boxprops: A dict containing names and values for the
        properties of the bounding boxes for the annotations I
        create. Based on defaults in I{_boxprops}.

    @cvar _boxprops: Default values for annotation object bounding box
        properties.

    @see: L{PlotHelper.addAnnotations} and
        L{PlotHelper.updateAnnotations}.
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
    radii = [1.5, 2.5, 4.0, 6.0, 10.0, 12.0]
    
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
    # Set True to show positioning rectangles
    verbose = True
    
    @classmethod
    def setVerbose(cls, yes=True):
        cls.verbose = yes
    
    def __init__(self, ax, pairs, **kw):
        self.ax = ax
        self.annotations = []
        self.pos = PositionEvaluator(ax, pairs, self.annotations)
        for name in kw:
            setattr(self, name, kw[name])
        self.boxprops = self._boxprops.copy()
        self.boxprops['boxstyle'] = sub(
            "round,pad={:0.3f}", self._paddingForSize())
        self.db = None
    
    def _paddingForSize(self):
        """
        Returns the amount of padding (in what units???) for the bounding
        boxes of all annotations I produce, given my I{fontsize}.
        """
        fs = self.fontsize
        if fs in self.fontsizeMap:
            fs = self.fontsizeMap[fs]
        return min([0.25, 0.44 - 0.008*fs])
    
    def _offseterator(self):
        """
        Iterates over possible annotation offset positions, rotating
        clockwise around a central point.

        After one full rotation, another rotation is done at a larger
        offset radius. Once the radius get big enough, the box
        positions include not just 45-degree points on the compass,
        but also points in between.

        Each iteration yields a 2-tuple with (1) the horizontal offset
        I{dx} in pixels to the right of the data point, and (2) the
        vertical offset I{dx} in pixels above the data point.
        """
        def scaleOffset(radius, dx, dy):
            return radius*dx, radius*dy
        
        for radius in self.radii:
            for k, offset in enumerate(self.offsets):
                yield scaleOffset(radius, *offset)
                if radius > 2:
                    yield scaleOffset(radius, *self.moreOffsets[k])

    def add(self, x, y, text, dx=0, dy=0):
        """
        Adds an annotation with an arrow pointing at data-value
        coordinates I{x} and I{y} and displaying the supplied I{text}
        inside a round-bordered text box.

        The annotation will be added to my Matplotlib C{Axes} object
        I{ax} right on top of its data-value coordinates. Obviously,
        it can't stay there, so you need to call L{update} to move it
        to an appropriate place once the rest of the subplot has been
        added. You also should call L{update} if the annotation needs
        to be repositioned due to a change in the figure dimensions.

        The keywords I{dx} and I{dy} are specified (in pixels) when
        this method gets called again by L{_move} to intelligently
        reposition an annotation by replacing it with a new one.

        Returns a reference to the new Matplotlib annotation object.
        """
        arrowprops = self.arrowprops.copy()
        ann = self.ax.annotate(
            text, xy=(x, y), xytext=(dx, dy), textcoords="offset pixels",
            size=self.fontsize, weight=self.fontWeight,
            arrowprops=arrowprops, bbox=self.boxprops,
            ha='center', va='center', zorder=100)
        ann.draw(self.ax.figure.canvas.get_renderer())
        self.annotations.append(ann)
        return ann
    
    def _move(self, ann, dx, dy):
        """
        Moves the supplied annotation by setting its text position to
        I{dx} and I{dy}.
        """
        x, y = ann.xy
        text = ann.get_text()
        ann.set_position((dx, dy))
        
    def update(self, *args, **kw):
        """
        Call this to have all added annotations intelligently
        repositioned.

        All arguments and keywords are accepted but disregarded,
        making this is a convenient GUI hook or Twisted callback.

        Returns C{True} if anything was repositioned, C{False} if
        everything stayed the same. You can use that info to decide
        whether to redraw.
        """
        replaced = set()
        db = DebugBoxer(self.ax.get_figure()) if self.verbose else None
        for ann in self.annotations:
            dx0, dy0 = getOffset(ann)
            best = (float('+inf'), dx0, dy0)
            for dx, dy in self._offseterator():
                score, rr = self.pos.score(ann, dx, dy)
                if db: db.add(rr)
                if not score: break
                if score < best[0]: best = (score, dx, dy)
            else:
                # No clear position found, use the least bad one
                dx, dy = best[1:]
            if (dx, dy) != (dx0, dy0):
                # The best position changed, so an update is needed
                replaced.add(self._move(ann, dx, dy))
        for ann in replaced:
            if ann in self.annotations:
                self.annotations.remove(ann)
        return bool(replaced)
