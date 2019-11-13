#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# yampex:
# Yet Another Matplotlib Extension
#
# Copyright (C) 2017-2019 by Edwin A. Suominen,
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

# Twisted dependency is only for its excellent trial unit testing tool
from twisted.trial.unittest import TestCase

from yampex import annotate


class MockAxes(object):
    """
    A stand-in for the Matplotlib C{Axes} object.
    """
    @property
    def transData(self):
        return self

    def transform(self, xy):
        # TODO

    
class MockAnnotation(object):
    """
    A stand-in for the Matplotlib C{Annotation} object.
    """
    x0 = -1
    x1 = +1
    y0 = -1
    y1 = +1
    
    def __init__(self, x, y):
        self.xy = x, y

    @property
    def axes(self):
        return MockAxes()


class Test_RectangleRegion(TestCase):
    def test_overlaps_point(self):
        
        
