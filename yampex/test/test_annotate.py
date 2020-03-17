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
Unit tests for L{annotate}.
"""

import numpy as np

# Twisted dependency is only for its excellent trial unit testing tool
from twisted.trial.unittest import TestCase

from yampex import annotate as a
from yampex import helper as h


def dataToPixels(z):
    """
    Given a data-point value I{z} along the x (or y) axis, returns the
    number of pixels from the left (or bottom) of the subplot.
    """
    return 250*(z+1.0)


class MockBBox(object):
    """
    A mock Matplotlib bounding box for a L{MockAnnotation} or window
    extents of a L{MockAxes}.
    """
    def __init__(self, xy, xytext, width, height):
        self._xy = xy
        self._xytext = xytext
        self.width = width
        self.height = height
    
    def get_extents(self):
        return self

    def get_points(self):
        """
        This is a method of the object ostensibly returned from a call to
        L{get_extents}.
        """
        x, y = [dataToPixels(z) for z in self._xy]
        x0 = x + self._xytext[0] - 0.5*self.width
        y0 = y + self._xytext[1] - 0.5*self.height
        x1 = x + self._xytext[0] + 0.5*self.width
        y1 = y + self._xytext[1] + 0.5*self.height
        return (x0, y0), (x1, y1)


class MockFigure(object):
    """
    A stand-in for the Matplotlib C{Figure} object. I have a 10-pixel
    border around my single fake subplot, resulting in dimensions of
    520x520 pixels.
    """
    def get_renderer(self):
        """
        No renderer is actually needed for testing.
        """
        return

    def get_window_extent(self):
        return MockBBox((0,0), (0,0), 520, 520)


class MockAxes(object):
    """
    A stand-in for the Matplotlib C{Axes} object.

    My fake x and y axes start at (-1,-1) at the lower left and end at
    (+1,+1) at the upper right, with 500 pixels of both width and
    height.
    """
    @property
    def transData(self):
        return self

    @property
    def figure(self):
        return MockFigure()

    def transform(self, xy):
        if len(xy) == 2:
            return [dataToPixels(z) for z in xy]
        return dataToPixels(xy)

    def get_window_extent(self):
        return MockBBox((0,0), (0,0), 500, 500)


class MockAnnotation(object):
    """
    A mock Matplotlib C{Annotation} object pointing to a data-point
    location of I{x}, I{y}, centered at an offet of I{dx}, I{dy}
    pixels.

    The annotation pretends to be in a subplot defined by
    L{MockAxes}. Its text is always "XXX".
    """
    def __init__(self, x=0, y=0, dx=0, dy=0, width=20, height=8):
        self.xy = x, y
        self.xytext = dx, dy
        self.width = width
        self.height = height

    @property
    def axes(self):
        return MockAxes()

    def get_position(self):
        return self.xytext

    def get_text(self):
        return "XXX"

    def get_bbox_patch(self):
        return MockBBox(self.xy, self.xytext, self.width, self.height)

    def draw(self, renderer):
        """
        No drawing is done in testing.
        """
        pass
        

class Test_RectangleRegion(TestCase):
    """
    Unit tests for L{RectangleRegion}.
    """
    def test_arrow_line(self):
        rr = a.RectangleRegion(MockAnnotation(), 0, 0, 10, 10)
        Axy, Cxy = rr.arrow_line
        self.assertEqual(Axy, (250, 250))
        self.assertEqual(Cxy, (250, 250))
        rr = a.RectangleRegion(MockAnnotation(0.1, 0.1), 15, 10, 10, 10)
        Axy, Cxy = rr.arrow_line
        self.assertEqual(Axy, (275, 275))
        self.assertEqual(Cxy, (290, 285))
        
    def test_overlaps_point(self):
        rr = a.RectangleRegion(MockAnnotation(), 4, 4, 10, 10)
        self.assertTrue(rr.overlaps_point(250, 250))
        self.assertTrue(rr.overlaps_point(255, 255))
        self.assertFalse(rr.overlaps_point(280, 250)) # Right
        self.assertFalse(rr.overlaps_point(250, 280)) # Above
        self.assertFalse(rr.overlaps_point(230, 250)) # Left
        self.assertFalse(rr.overlaps_point(250, 230)) # Below
        
    def test_overlaps_other(self):
        def yes(rr1, rr2):
            self.assertTrue(rr1.overlaps_other(rr2))
            self.assertTrue(rr2.overlaps_other(rr1))
            
        def no(rr1, rr2):
            self.assertFalse(rr1.overlaps_other(rr2))
            self.assertFalse(rr2.overlaps_other(rr1))
        
        rr1 = a.RectangleRegion(MockAnnotation(), 0, 0, 20, 10)
        rr2 = a.RectangleRegion(MockAnnotation(), 18, 0, 20, 10) # Right 18
        yes(rr1, rr2)
        rr3 = a.RectangleRegion(MockAnnotation(), 25, 0, 20, 10) # Right 25
        no(rr1, rr3)
        yes(rr2, rr3)
        rr4 = a.RectangleRegion(MockAnnotation(), 0, 8, 20, 10) # Up 8
        yes(rr1, rr4)
        no(rr3, rr4)
        rr4 = a.RectangleRegion(MockAnnotation(), 0, 20, 20, 10) # Up 20
        for rr in rr1, rr2, rr3:
            no(rr4, rr)

    def test_overlaps_other_20x8(self):
        """
        With dims and positions used in
        L{Test_PositionEvaluator.test_with_others}::

                                     5
                                     4
                                     3
                                     2             (267,261)
                                  +-------------------+
                                  |  0                |
                                  |  9                |
                                  |  8                |
                                  |  7   (257,257)    |
                                  |  6                |
                                  |  5                |     (275,254)
                                  |  4    +-----------|-------+
                       (247,253)  +-------------------+       |
                                     2    |                   |
                                     1    |                   |
        9876543210987654321012345678901234|6789012345678901234|678
                                     9    |      (265,0)      |
                                     8    |                   |
                                     7    |                   |
                                     6    +-------------------+
                                     5  (255,246)
                                     4
        """
        rr1 = a.RectangleRegion(MockAnnotation(), 15, 0, 20, 8)
        rr2 = a.RectangleRegion(MockAnnotation(), 7,  7, 20, 8)
        self.assertTrue(rr1.overlaps_other(rr2))
        self.assertTrue(rr2.overlaps_other(rr1))

    def test_overlaps_line(self):
        def xyp(x, y):
            return [250+z for z in (x, y)]
        
        def yes(xa, ya, xb, yb):
            self.assertTrue(rr.overlaps_line(xyp(xa, ya), xyp(xb, yb)))

        def no(xa, ya, xb, yb):
            self.assertFalse(rr.overlaps_line(xyp(xa, ya), xyp(xb, yb)))

        # Rectangular region with lower left at (-10,-5) and upper
        # right at (+10,+5).
        rr = a.RectangleRegion(MockAnnotation(), 0, 0, 20, 10)
        # Vertical lines
        no(-15, -15, -15, +15) # To the left
        no(+15, -15, +15, +15) # To the right
        yes(+5, -15, +5, +15) # Slightly off center
        # Horizontal lines
        no(-40, 0, -30, 0) # To the left
        no(+30, 0, +40, 0) # To the right
        yes(-30, +3, -5, +3) # Extending in from the left
        yes(+5, -3, +25, -3) # Extending in from the right
        no(-40, +8, +40, +8) # Above
        no(-40, -8, +40, -8) # Below
        # Ascending lines
        no(0, +8, +15, +16) # Entirely above
        no(-20, 0, +0, +18) # Above and to the left
        yes(-20, 0, +0, +9) # Not enough above and to the left
        yes(-100, -100, +100, +100) # Straight thru middle
        yes(0, -10, +20, +0) # Not enough above and to the left
        no(0, -18, +20, +0) # Below and to the right
        no(-15, -16, 0, -8) # Entirely below
    
    def test_overlaps_arrow(self):
        # "Midway, lower", overlaps the other one's line
        dx1, dy1 = 30, -30
        w1, h1 = 89.41, 18.785
        ann1 = MockAnnotation(0.01, -0.0899, dx1, dy1, w1, h1)
        rr1 = a.RectangleRegion(ann1, dx1, dy1, w1, h1)
        # "Near Midway, lower", vertical line overlaps the other
        # annotation
        dx2, dy2 = 0, -71
        w2, h2 = 120.785, 18.785
        ann2 = MockAnnotation(0.01, -0.0899, dx2, dy2, w2, h2)
        rr2 = a.RectangleRegion(ann2, dx2, dy2, w2, h2)
        self.assertTrue(rr1.overlaps_line(*rr2.arrow_line))

        
class Test_PositionEvaluator(TestCase):
    """
    Unit tests for L{PositionEvaluator}.
    """
    def setUp(self):
        self.ax = MockAxes()
        pair = h.Pair()
        pair.X = np.linspace(-1, +1, 100)
        pair.Y = np.linspace(-1, +1, 100)
        self.pairs = h.Pairs()
        self.pairs.append(pair)

    def test_with_boundary(self):
        ann = MockAnnotation()
        pos = a.PositionEvaluator(self.ax, self.pairs, [ann])
        #--- Right in middle ---------------------------------------------
        rr = a.RectangleRegion(ann, 0, 0, 20, 8)
        self.assertEqual(pos.with_boundary(rr), 0)
        #--- To the right ------------------------------------------------
        # Near but not touching right boundary
        rr = a.RectangleRegion(ann, 238, 0, 20, 8)
        self.assertEqual(pos.with_boundary(rr), 0)
        # Overlaps right subplot boundary  but not figure boundary
        rr = a.RectangleRegion(ann, 245, 0, 20, 8)
        self.assertEqual(pos.with_boundary(rr), 3)
        # Overlaps right subplot boundary and figure boundary
        rr = a.RectangleRegion(ann, 255, 0, 20, 8)
        self.assertEqual(pos.with_boundary(rr), 9)
        #--- Below -------------------------------------------------------
        # Near but not touching bottom boundary
        rr = a.RectangleRegion(ann, 100, -230, 20, 8)
        self.assertEqual(pos.with_boundary(rr), 0)
        # Overlaps bottom subplot boundary but not figure boundary
        rr = a.RectangleRegion(ann, 100, -248, 20, 8)
        self.assertEqual(pos.with_boundary(rr), 3)
        # Overlaps bottom subplot boundary and figure boundary
        rr = a.RectangleRegion(ann, 100, -257, 20, 8)
        self.assertEqual(pos.with_boundary(rr), 9)

    def test_with_others(self):
        """
                              |           O
              NW: (-15, 14)   |         O
              SE: (5,6)       |       O
                        +------+    O
                        | ann2 |>>O      (25,+4)
                        +------+O+------+
            ------------------O<<| ann1 |-----------------------
                            O |  +------+
                          O   | (5,-4)
                  y=x   O     |

        """
        def rr(dx, dy):
            return a.RectangleRegion(ann3, dx, dy, 20, 8)
        
        ann1 = MockAnnotation(0.0, 0.0, 15, 0)
        ann2 = MockAnnotation(0.04, 0.04, -15, 0)
        ann3 = MockAnnotation(0.0, 0.0)
        annotations = [
            # Axy = (250, 250), Cxy = (265, 250)
            ann1,
            # Axy = (260, 260), Cxy = (245, 260)
            ann2,
            # Axy = (250, 250)
            ann3,
        ]
        pos = a.PositionEvaluator(self.ax, self.pairs, annotations)
        # Above and to the right, overlaps with both ann1 and ann2,
        # and also arrow line of ann2
        self.assertEqual(pos.with_others(rr(20, 6), ann3), 10.0)
        # Below and to the right, overlaps with ann1 and its arrow line
        self.assertEqual(pos.with_others(rr(7, -7), ann3), 6.0)
        # Straight below, no overlaps
        self.assertEqual(pos.with_others(rr(0, -14), ann3), 0.0)
        
    def test_with_data(self):
        def rr(dx, dy):
            return a.RectangleRegion(ann, dx, dy, 20, 8)

        ann = MockAnnotation(0.0, 0.0)
        pos = a.PositionEvaluator(self.ax, self.pairs, [ann])
        # Overlaps data, not far enough to the right
        self.assertEqual(pos.with_data(rr(12, 0)), 1.0)
        # Further to the right, no overlap
        self.assertEqual(pos.with_data(rr(19, 0)), 0.0)
        # Straight below, overlaps
        self.assertEqual(pos.with_data(rr(0, -5)), 1.0)
        # Above and to the left, no overlap
        self.assertEqual(pos.with_data(rr(-10, +10)), 0.0)
        
        
        
