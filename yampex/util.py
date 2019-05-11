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
Utility stuff.
"""

# CAUTION: The errorbar plot doesn't yet work via the subplotter
# object. Access the underlying Matplotlib Axes object directly with
# sp().ax
PLOTTER_NAMES = {
    'plot', 'scatter',
    'loglog', 'semilogx', 'semilogy',
    'pie', 'plot_date', 'vlines', 'hlines',
    'step', 'bar', 'barh', 'broken_barh', 'errorbar', 'stem',
    'fill_between', 'fill_betweenx', 'eventplot', 'stackplot',
}


def sub(proto, *args):
    """
    This really should be a built-in function.
    """
    return proto.format(*args)

