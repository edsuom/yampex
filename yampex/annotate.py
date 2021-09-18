#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# yampex:
# Yet Another Matplotlib Extension
#
# Copyright (C) 2017-2021 by Edwin A. Suominen,
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

    Obtaining the exact size of annotation objects has proved
    computationally very difficult. Many, many retries were
    required. Switched to just estimating.
    """
    def __init__(self):
        self.tsc = TextSizeComputer()

    def area(self, dims):
        return dims[0] * dims[1]
        
    def __call__(self, ann):
        return self.tsc.dims(ann)


class RectangleRegion(object):
    """
    I am a rectangular plot region where an annotation or textbox is
    or might go.

    Construct me with the C{Axes} object I{ax} for the annotation or
    textbox, along with its center position I{xy}, I{width}, and
    I{height}. For an annotation, also include the number of pixels to
    the right I{dx} and up I{dy} from that annotation's data-point
    location to the center of the proposed location.

    For an annotation, the positioning of the region is like so, with
    "A" being the annotation's data-point location, "C" being the
    center of my rectangular region::

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
    
    def __init__(self, ax, xy, width, height, dx, dy):
        self.Ax, self.Ay = ax.transData.transform(xy)
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

    def overlaps_obj(self, obj):
        """
        Returns C{True} if I overlap the supplied Matplotlib I{obj} having
        a C{get_window_extent} method.

        If there is not yet a renderer, the overlap cannot be
        determined and so C{False} is returned.
        """
        try:
            other = obj.get_window_extent()
        except: return False
        return self._xOverlap(other) and self._yOverlap(other)


class PositionEvaluator(object):
    """
    Use an instance of me to evaluate the overlap score of a proposed
    position of an annotation, based on subplot data, boundaries, and
    the positions of all other annotations in the subplot.
    
    All subplot data is converted to, and computations done in, pixel
    units.
    """
    # Cutoff for not bothering to compute further score increases
    awful = 100
    # Score increase for overlap with axis or figure boundary
    weight_boundary = 3.0
    # Score increase for overlap with another annotation's text box
    weight_tb = 4.0
    # Score increase for overlap with another annotation's arrow line
    weight_arrow = 2.0
    # Score increase for overlap with data points
    weight_data = 1.0
    # Score increase for overlap with other Matplot objects
    weight_obj = 4.0
    # Score penalty for unrealistic other-annotation size (hopefully
    # not needed much)
    size_penalty = 3.0
    
    def __init__(self, ax, pairs, annotations):
        self.ax = ax
        self.pairs = pairs
        self.annotations = annotations
        self.sizer = Sizer()
        self.avoided = set()

    def avoid(self, obj):
        """
        Call to have annotations avoid the region defined by any supplied
        Matplotlib obj having a C{get_window_extent} method.
        """
        if not hasattr(obj, 'get_window_extent'):
            raise TypeError(sub(
                "Supplied object {} has no 'get_window_extent' method!", obj))
        self.avoided.add(obj)

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
                score += self.weight_boundary*(k+1)
            else: return score
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
            size = self.sizer(ann_other)
            if size is None:
                # Unfortunately, we can't assess overlap if the
                # other's size can't be realistically determined. So
                # the best thing to do is give this position a penalty
                # and move on to check overlap with the next existing
                # annotation
                score += self.size_penalty
                continue
            width, height = size
            rr_other = RectangleRegion(
                ann_other.axes, ann_other.xy, width, height, dx, dy)
            if rr.overlaps_other(rr_other):
                # Proposed rr overlaps the other annotation's text box
                score += self.weight_boundary
            if rr.overlaps_line(*rr_other.arrow_line):
                # Proposed rr overlaps the other annotation's arrow line
                score += self.weight_arrow
            if rr_other.overlaps_line(*rr.arrow_line):
                # Proposed annotation's arrow line overlaps the other
                # annotation's text box
                score += self.weight_arrow
            if score > self.awful:
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
                        score += self.weight_data
                        break
                    if xy[0] > rr.x1:
                        # Any remaining segments are entirely to the
                        # right of the rectangle region
                        break
                xy_prev = xy
            if score > self.awful: break
        return score

    def with_avoided(self, rr):
        """
        Returns score for the proposed L{RectangleRegion} I{rr} possibly
        overlapping with Matplotlib objects that have been registered
        to avoid with calls to L{avoid}.

        The score increases with the number of overlaps.
        """
        score = 0.0
        for obj in self.avoided:
            if rr.overlaps_obj(obj):
                score += self.weight_obj
                if score > self.awful: break
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
        location in my subplot, or B{None} if no realistic size can be
        determined for the region.

        Sometimes my L{Sizer} simply cannot provide a realistic
        estimate of the annotation's size. When the estimated size is
        too small to be realistic, no L{RectangleRegion} is
        constructed and C{None} is returned instead of the
        2-tuple. Weirdly, a realistic size will often be computed at a
        different position, so the workaround is to just proceed with
        the next candidate position and re-do the score for this one
        once a realistic size has been determined.
        """
        size = self.sizer(ann)
        if size is None:
            return
        width, height = size
        rr = RectangleRegion(ann.axes, ann.xy, width, height, dx, dy)
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
        score += self.with_avoided(rr)
        return score, rr


class DebugBoxer(object):
    """
    I draw a colored box at to visually represent L{RectangleRegion}
    instances for debugging purposes.

    The boxes are unfilled rectangles with colors following the
    resistor color code indexed from 1, with the first attempted
    position being drawn in brown (#1), the second being red (#2),
    etc.

    By default, all boxes are in a single group (ID=0) and will all be
    removed when the color is reset with a call to
    L{resetColor}. However, you can specify different color groups
    with a call to L{newGroup} and then use the returned ID as an
    argument to L{resetColor}. Then only that group will have its
    color reset and its boxes removed. Any subsequent calls to L{add}
    will be for that group until there is another call to L{resetColor}.
    """
    colors = ['brown', 'red', 'orange', 'yellow', 'green', 'blue', 'violet']

    def __init__(self, ax):
        self.ax = ax
        self.K = {}
        self.patches = {}

    def ann2ID(self, ann):
        return id(ann)
        
    def newGroup(self, ann):
        ID = self.ann2ID(ann)
        self.patches[ID] = []
        self.K[ID] = -1
        
    def resetColor(self, ann):
        self.ID = self.ann2ID(ann)
        self.K[self.ID] = -1
        self.bb = self.ax.get_window_extent()
        for patch in self.patches[self.ID]:
            if patch in self.ax.patches:
                self.ax.patches.remove(patch)
    
    def add(self, rr):
        """
        Adds a debugging box to my figure at the position of the supplied
        L{RectangleRegion} object I{rr}.
        """
        ID = self.ID
        self.K[ID] = (self.K[ID] + 1) % len(self.colors)
        xy = [rr.x0, rr.y0]
        if xy[0] < self.bb.xmin: return
        if xy[1] < self.bb.ymin: return
        width = rr.x1-rr.x0
        if xy[0]+width > self.bb.xmax: return
        height = rr.y1-rr.y0
        if xy[1]+height > self.bb.ymax: return
        print("ADD:", xy, width, height)
        patch = patches.Rectangle(
            xy, width, height, color=self.colors[self.K[ID]], fill=False)
        self.ax.patches.append(patch)
        self.patches[ID].append(patch)


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
    radii = [1.5, 2.5, 3.5, 5.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 14.0]
    
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
        self.db = DebugBoxer(self.ax) if self.verbose else None

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

    def avoid(self, obj):
        """
        Call to have annotations avoid the region defined by any supplied
        Matplotlib obj having a C{get_window_extent} method.
        """
        self.pos.avoid(obj)
                    
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
        if self.db: self.db.newGroup(ann)
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
        try_agains = []
        replaced = set()
        for ann in self.annotations:
            if self.db: self.db.resetColor(ann)
            dx0, dy0 = getOffset(ann)
            best = (float('+inf'), dx0, dy0)
            for dx, dy in self._offseterator():
                score_rr = self.pos.score(ann, dx, dy)
                if score_rr is None:
                    # No realistic size (and thus no candidate score
                    # or rr) was obtained. We will try this position
                    # again later
                    try_agains.append((dx, dy))
                    continue
                score, rr = score_rr
                if self.db: self.db.add(rr)
                if not score: break
                if score < best[0]: best = (score, dx, dy)
            else:
                # No clear position found, use the least bad one
                dx, dy = best[1:]
            # Now try again those that we couldn't determine the first time
            for dx, dy in try_agains:
                score_rr = self.pos.score(ann, dx, dy)
                if score_rr is None:
                    # Hopefully this rarely happens, if ever
                    continue
                score, rr = score_rr
                if self.db: self.db.add(rr)
                if score <= best[0]: best = (score, dx, dy)
            if (dx, dy) != (dx0, dy0):
                # The best position changed, so an update is needed
                replaced.add(self._move(ann, dx, dy))
        for ann in replaced:
            if ann in self.annotations:
                self.annotations.remove(ann)
        return bool(replaced)
