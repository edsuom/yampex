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

    
class PlotHelper(object):
    """
    I help with plotting calls for a single subplot.
    """
    settings = {'title', 'xlabel', 'ylabel'}

    __slots__ = ['ax', 'p']
    
    def __init__(self, ax, p):
        self.ax = ax
        self.p = p

    def __getattr__(self, name):
        """
        You can access any of my L{Plotter} object's attributes as my own,
        except that my reference I{p} to it, I{ax}, and I{settings}
        are mine.
        """
        return getattr(self.p, name)
            
    def parseArgs(self, args):
        """
        Parses the supplied I{args} into vectors. Returns the a list of
        the vectors and their names if the args were container item
        reference strings, or C{None} if they were vectors all along.
        
        Pops the first arg and uses it as a container if it is a container
        (e.g., a dict, not a Numpy array) and the remaining args are
        all strings referencing items that are in that
        container. Makes the remaining args into vectors if they are
        references to container items.
        """
        def arrayify(x):
            if isinstance(x, (str, np.ndarray)):
                return x
            return np.array(x)
        
        vectors = []
        if not isinstance(args[0], (list, tuple, np.ndarray)):
            V = args[0]
            names = args[1:]
            for name in names:
                vectors.append(arrayify(V[name]))
            return vectors, names
        if self.V is not None:
            names = []
            for arg in args:
                if isinstance(arg, str) and arg in self.V:
                    names.append(arg)
                    vectors.append(arrayify(self.V[arg]))
                else:
                    names.append(None)
                    vectors.append(arrayify(arg))
            if None in names:
                names = None
            return vectors, names
        return [arrayify(x) for x in args], None

    def doSettings(self):
        """
        Does C{set_XXX} calls on ...
        """
        def bbAdd(textObj):
            dims = self.adj.textDims(textObj)
            self.dims.setdefault(k, {})[name] = dims

        k = self.sp.kLast
        for name in self.settings:
            value = self.opts[name]
            #import pdb; pdb.set_trace()
            if not value: continue
            fontsize = self.opts['fontsizes'].get(name, None)
            kw = {'size':fontsize} if fontsize else {}
            bbAdd(self.sp.set_(name, value, **kw))
            if name == 'xlabel':
                self.xlabels[k] = value
                continue
        settings = self.opts['settings']
        for name in settings:
            bbAdd(self.sp.set_(name, settings[name]))
