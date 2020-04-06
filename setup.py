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


NAME = "yampex"


### Imports and support
from setuptools import setup

### Define requirements
required = ['numpy', 'matplotlib', 'screeninfo']


### Define setup options
kw = {'version':'0.9.6',
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
      'packages':[
          'yampex', 'yampex.scripts', 'yampex.examples', 'yampex.test'],
      'entry_points': {
          'console_scripts': [
              'yampex-examples = yampex.scripts.examples:extract',
          ],
      },
      'zip_safe':True,
      'long_description_content_type': "text/markdown",
}

kw['keywords'] = [
    'matplotlib', 'numpy',
    'extension', 'subplots', 'annotations', 'plots', 'plotting',
]


kw['classifiers'] = [
    'Development Status :: 4 - Beta',

    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',

    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Scientific/Engineering :: Visualization',
]


# You get 77 characters. Use them wisely.
#----------------------------------------------------------------------------
#        10        20        30        40        50        60        70
#2345678901234567890123456789012345678901234567890123456789012345678901234567
kw['description'] = " ".join("""
Yet Another Matplotlib Extension, with simplified subplotting & annotations.
""".split("\n"))

kw['long_description'] = """
The yampex package makes [Matplotlib](https://matplotlib.org/) much
easier to use, especially with subplots. You simply construct a
[Plotter](http://edsuom.com/yampex/yampex.plot.Plotter.html) object
with the number of subplots or subplot rows and columns you want, and
do a context call on it to get a version of the object that's all set
up to do your subplots.

A powerful option-setting API lets you easily and intuitively
configure all of your subplots globally and specific subplots locally.

You can easily add annotations to your plots. They get placed
intelligently, in a way that minimizes visual disruption.

Comes with a number of small and informative [example
files](http://edsuom.com/yampex/yampex.examples.html), which you can
install to a *yampex-examples* subdirectory of your home directory by
typing `yampex-examples` as a shell command. Go there and you can run
each example as a Python script, or all of them with the *runall.sh*
shell script.

There's also a quick example on the project
[page](http://edsuom.com/yampex.html) at **edsuom.com**.

"""

### Finally, run the setup
setup(name=NAME, **kw)
print("\n" + '-'*79)
print("To create a subdirectory 'yampex-examples' of example files")
print("in the current directory, you may run the command 'yampex-examples'.")
print("It's not required to use the yampex package, but you might find")
print("it instructive.\n")

