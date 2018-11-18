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


NAME = "yampex"


### Imports and support
from setuptools import setup

### Define requirements
required = ['numpy', 'matplotlib',]


### Define setup options
kw = {'version':'0.8.3',
      'license':'Apache License (2.0)',
      'platforms':'OS Independent',

      'url':"http://edsuom.com/{}.html".format(NAME),
      'project_urls':      {
          'GitHub':     "https://github.com/edsuom/{}".format(NAME),
          'API':        "http://edsuom.com/{}/{}.html".format(
              NAME, NAME.lower()),
          },
      'author':"Edwin A. Suominen",
      'author_email':"foss@edsuom.com",
      'maintainer':'Edwin A. Suominen',
      'maintainer_email':"foss@edsuom.com",
      
      'install_requires':required,
      'packages':['yampex',],
      
      'zip_safe':True,
}

kw['keywords'] = [
    'matplotlib', 'numpy',
    'extension', 'subplots', 'annotations', 'plotting',
]


kw['classifiers'] = [
    'Development Status :: 4 - Beta',

    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Framework :: Twisted',

    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Scientific/Engineering :: Visualization',
]


kw['description'] = " ".join("""
Yet Another Matplotlib Extension, with simplified subplotting.
""".split("\n"))

kw['long_description'] = """
yampex makes Matplotlib_ easier to use, especially with subplots. You
simply construct a Plotter_ object with the number of subplot rows
and columns you want, and do a context call on it to get a version of
the object that's all set up to do your subplots.

There's a quick example on the project page_ at edsuom.com.

.. _Matplotlib: https://matplotlib.org/

.. _Plotter: http://edsuom.com/yampex/yampex.plot.Plotter.html

.. _page: http://edsuom.com/yampex.html

"""

### Finally, run the setup
setup(name=NAME, **kw)

