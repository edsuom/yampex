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
Comparison between two nonlinear functions.
"""

import numpy as np
from yampex import xy
from yampex.util import sub


def vd(Ex, Ec, vdm):
    Er = Ex/c
    return vdm*Er / np.sqrt(1 + Er**2)


def lowerlimit(vdd, vdm):
    a = 200*vdm
    ai = 1.0/a
    return ai*np.log(1 + np.exp(a*vdd))
    Y = np.empty_like(vdd)
    K = np.flatnonzero(vdd > 0)
    Y[K] = vdd[K] + ai*np.log(1+np.exp(-a*vdd[K]))
    K = np.flatnonzero(vdd <= 0)
    Y[K] = ai*np.log(1+np.exp(a*vdd[K]))
    return Y


def Ex(vd, Ec, vdm, limit=False):
    vdd = vdm-vd
    if limit: vdd = lowerlimit(vdd, vdm)
    return Ec*vd*(1.0/vdd - 1.0/vdm)


def run():
    Ec = 1.0
    vdm = 1.98
    VD = np.linspace(1.95, 2.0, 1000)
    K = np.flatnonzero(np.abs(VD-vdm) > 0.0001)
    VD = VD[K]
    E1 = Ex(VD, Ec, vdm)
    E2 = Ex(VD, Ec, vdm, limit=True)
    E2 = np.clip(E2, None, 2*E1.max())
    xy(VD, E1, E2)


if __name__ == '__main__':
    run()
