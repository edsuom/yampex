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

    @cvar margin: The number of pixels of whitespace to maintain
        outside the annotations' visible borders.
    """
    margin = 2
    
    def __init__(self, ann, dx, dy, width, height):
        self.ann = ann
        self.Ax, self.Ay = self.ann.axes.transData.transform(ann.xy)
        self.Cx = self.Ax + dx
        self.Cy = self.Ay + dy
        self.x0 = self.Cx - 0.5*width - self.margin
        self.x1 = self.Cx + 0.5*width + self.margin
        self.y0 = self.Cy - 0.5*height - self.margin
        self.y1 = self.Cy + 0.5*height + self.margin

    def __repr__(self):
        args = [int(round(x)) for x in (self.Ax, self.Ay)]
        for x in (self.x0, self.y0, self.x1, self.y1):
            args.append(int(round(x)))
        return sub("({:d}, {:d}) --> [{:d},{:d} {:d},{:d}]", *args)

    @property
    def arrow_line(self):
        """
        B{Property}: A 2-tuple with endpoints of the annotation's arrow
        line from its data point (Ax, Ay) to my center (Cx, Cy).
        """
        return (self.Ax, self.Ay), (self.Cx, self.Cy)
    
    def overlaps_point(self, x, y):
        """
        Returns C{True} if I overlap the point specified in pixels.
        """
        if x < self.x0 or x > self.x1:
            return False
        if y < self.y0 or y > self.y1:
            return False
        return True
    
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

    def overlaps_other(self, other):
        """
        Returns C{True} if I overlap the I{other} L{RectangleRegion}
        instance.
        """
        return self._xOverlap(other) and self._yOverlap(other)

    def overlaps_line(self, xya, xyb):
        """
        Returns C{True} if I overlap the line segment from I{xya} (xa,ya)
        to I{xyb} (xb,yb).
        """
        def y(x):
            return m*(x-xa) + ya

        xa, ya = xya
        xb, yb = xyb
        if xa > xb:
            # Swap so first segment is always to the left of the
            # second one
            return self.overlaps_line(xyb, xya)
        if self.x0 > xb or self.x1 < xa:
            # I am entirely to the left or right of the line segment
            return False
        if self.y0 > max([ya, yb]) or self.y1 < min([ya, yb]):
            # I am entirely above or below the line segment
            return False
        if xa == xb:
            # Special case: Vertical line, must overlap
            return True
        m = float(yb-ya) / (xb-xa)
        if ya < yb:
            # Ascending line segment
            if y(self.x0) > self.y1:
                # My NW corner is below and to the right of it
                return False
            if y(self.x1) < self.y0:
                # My SE corner is above and to the left of it
                return False
            # Overlaps
            return True
        # Descending line segment
        if y(self.x1) > self.y1:
            # My NE corner is below and to the left of it
            return False
        if y(self.x0) < self.y0:
            # My SW corner is above and to the right of it
            return False
        # Overlaps
        return True


class PositionEvaluator(object):
    """
    Use an instance of me to evaluate the overlap score of a proposed
    position of an annotation, based on subplot data, boundaries, and
    the positions of all other annotations in the subplot.
    
    All subplot data is converted to, and computations done in, pixel
    units.
    """
    awful = 100
    
    def __init__(self, ax, pairs, annotations):
        self.ax = ax
        self.pairs = pairs
        self.annotations = annotations
        self.sizer = Sizer()

    def with_boundary(self, rr):
        """
        Returns score for the proposed L{RectangleRegion} I{rr} possibly
        overlapping with (or going beyond) axis or figure boundary.

        The score is twice as high for an overlap with the figure
        boundary.
        """
        score = 0.0
        ax = self.ax
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
    
    def with_others(self, rr, ann):
        """
        Returns score for the proposed L{RectangleRegion} I{rr} possibly
        overlapping with any annotation other than the specified one
        I{ann}.

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
                # Proposed rr overlaps the other annotation's text box
                score += 4.0
            if rr.overlaps_line(*rr_other.arrow_line):
                # Proposed rr overlaps the other annotation's arrow line
                score += 2.0
            if rr_other.overlaps_line(*rr.arrow_line):
                # Proposed annotation's arrow line overlaps the other
                # annotation's text box
                score += 2.0
            if score >= self.awful:
                break
        return score

    def with_data(self, rr):
        """
        Returns score for the proposed L{RectangleRegion} I{rr} possibly
        overlapping with my subplot's X,Y data.

        The score increases with the number of plot lines overlapped.

        This is by far the slowest analysis to run when there is a
        typically large number of X,Y data points. However, it is made
        considerably more efficient by skipping overlap checking for a
        given set of X,Y data until the right end of the segment is to
        the right of the left side of I{rr}, and by quitting further
        checking after the right end of the segment goes beyond the
        right side of I{rr}.

        B{TODO}: Make even more efficient by using Numpy's testing and
        selection capabilities to select the relevant slice of X,Y
        data for possible segment overlap.
        """
        score = 0.0
        for pair in self.pairs:
            XY = pair.getXY(asArray=True)
            XY = self.ax.transData.transform(XY)
            xy_prev = None
            for xy in XY:
                if xy_prev is not None:
                    if xy[0] > rr.x0 and rr.overlaps_line(xy_prev, xy):
                        score += 1.0
                        break
                    if xy[0] > rr.x1:
                        # Any remaining segments are entirely to the
                        # right of the rectangle region
                        break
                xy_prev = xy
        return score
    
    def score(self, ann, dx, dy):
        """
        Computes the total overlap score for the annotation if it were
        positioned in my subplot at the specified offset I{dx} and
        I{dy} in pixels from its data point.

        A higher overlap score is worse. A zero overlap score (best
        case) indicates no overlap with anything else at that
        offset. My I{awful} score is considered as bad as it gets:
        There's no point in differentiating between it and anything
        worse.

        Returns a 2-tuple with the overlap score and the
        L{RectangleRegion} object I construct for its proposed
        location in my subplot.
        """
        width, height = self.sizer(ann)
        rr = RectangleRegion(ann, dx, dy, width, height)
        Axy, Cxy = rr.arrow_line
        if rr.overlaps_point(*Axy):
            # Overlaps its own data point
            return self.awful, rr
        # Modest penalty for awkwardly short arrow
        x, y = [0.8*Axy[k]+0.2*Cxy[k] for k in (0,1)]
        score = 1.0 if rr.overlaps_point(x, y) else 0.0
        score += self.with_boundary(rr)
        score += self.with_others(rr, ann)
        if score < self.awful:
            score += self.with_data(rr)
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
        self.resetColor

    def resetColor(self):
        self.k = -1
        
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
    radii = [1.5, 2.5, 3.5, 5.0, 7.0, 9.0, 11.0, 14.0]
    
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
    # Set True to draw positioning rectangles when updating annotations
    verbose = False
    
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

    def setVerbose(self, yes=True):
        self.verbose = yes
    
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
            if db: db.resetColor()
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
