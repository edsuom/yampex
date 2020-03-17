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
Tools for processing Numpy vectors before plotting.
"""

import numpy as np

from yampex.util import sub


def clipOutliers(sp, X, ratio, suffix, annEnd=False):
    """
    Clips the most positive and negative deviations of vector I{X} to
    the product of the supplied I{ratio} times the deviation between
    the second-most positive (or negative) value and the median. Adds
    annotations to subplotting context tool I{sp} indicating the
    true value of the clipped points.

    Set I{annEnd} C{True} to add an annotation at the end of the
    subplot.

    Call your context tool I{sp} with the clipped result however you
    wish, and the subplot will have the annotations.
    """
    def Xdev(X):
        if sign == 1:
            return X - Xmedian
        else: return Xmedian - X

    def withSuffix(x):
        return sub("{:+.2f}{}", x, suffix)
    
    sign = -1
    Xmedian = np.median(X)
    I = np.argsort(X)
    for kMost, kNext in ((I[0], I[1]), (I[-1], I[-2])):
        Xmost = X[kMost]
        Xnext = X[kNext]
        if Xdev(Xmost) > ratio*Xdev(Xnext):
            X[kMost] = Xmedian + sign*ratio*Xdev(Xnext)
            sp.set_axisExact('y')
            sp.add_annotation(kMost, withSuffix(Xmost))
        sign *= -1
    if annEnd:
        sp.add_annotation(-1, withSuffix(X[-1]))
    return X
