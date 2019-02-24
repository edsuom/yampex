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

    __slots__ = ['ax', 'p', 'vectors', 'names', 'stringArg']
    
    def __init__(self, ax, p):
        self.ax = ax
        self.p = p
        self.vectors = []
        self.names = []
        self.stringArg = False

    def __len__(self):
        """
        My length is the number of vectors (and names) I'm holding.
        """
        return len(self.vectors)
        
    def __getattr__(self, name):
        """
        You can access any of my L{Plotter} object's attributes as my own
        whose names don't conflict with those of my own attributes.

        Best to refer to I{p} directly, though. This is a messy crutch.
        """
        return getattr(self.p, name)

    def _isDuplicateX(self, X):
        """
        Returns C{True} if I have at least one vector and I{X} is, or is a
        duplicate of, the first one.
        """
        if not self.vectors: return
        X0 = self.vectors[0]
        if X is X0: return True
        if X.shape != X0.shape: return
        return np.all(np.equal(X, X0))
    
    def addVector(self, X, scale=None):
        """
        Appends I{X}, converted to a 1-D Numpy array if it's not one
        already or a string, to my I{vectors} list.
        """
        if not isinstance(X, np.ndarray):
            X = np.array(X)
        if scale: X *= scale
        self.vectors.append(X)
    
    def parseArgs(self, args):
        """
        Parses the supplied I{args} into vectors. Appends the vectors to
        my I{vectors} list and the names to my I{names} list.
        
        Pops the first arg and uses it as a container if it is a
        container (e.g., a dict, not a Numpy array). Otherwise, refers
        to the I{V} attribute of my L{Plotter} I{p} as a possible
        container. If there is indeed a container, and the remaining
        args are all strings referencing items that are in it, makes
        the remaining args into vectors.

        Each item of my I{names} list is a string with the name of a
        vector at the same index of I{vectors}, or C{None} if that
        vector was supplied as-is and thus no name name was available.
        """
        args = list(args)
        if not isinstance(args[0], (list, tuple, np.ndarray)):
            V = args.pop(0)
        else: V = self.p.V
        for k, arg in enumerate(args):
            if isinstance(arg, str):
                if V is not None and arg in V:
                    name = arg
                    X = V[arg]
                else:
                    self.stringArg = True
                    name = None
                    self.vectors.append(arg)
                    continue
            else:
                name = None
                X = arg
            if k == 0:
                if self._isDuplicateX(X):
                    continue
                scale = self.p.opts['xscale']
            else: scale = None
            self.names.append(name)
            self.addVector(X, scale)

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
