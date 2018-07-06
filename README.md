## yampex
*Yet Another Matplotlib Extension, with simplified subplotting*

* [API Docs](http://edsuom.com/yampex/yampex.html)
* [PyPI Page](https://pypi.python.org/pypi/yampex/)
* [Project Page](http://edsuom.com/yampex.html) at **edsuom.com**

*yampex* makes Matplotlib easier to use, especially with subplots. You
simply construct a `Plotter` object with the number of subplot rows
and columns you want, and do a context call on it to get a version of
the object that's all set up to do your subplots. Like this:

    import numpy as np
    from yampex import Plotter
    
    funcNames = ('sin', 'cos', width=7, height=5)
    X = np.linspace(0, 4*np.pi)
    pt = Plotter(1, 2)
    pt.set_xlabel("X"); pt.set_grid()
    with pt as p:
        for funcName in funcNames:
            Y = getattr(np, funcName)(X)
            p.set_ylabel("{}(X)".format(funcName))
            p(X, Y)
    pt.show("Sin and Cosine")
    
The `Plotter` instance `pt` has various methods for setting plot
modes. The example calls two of them before it makes the context call,
thus affecting *all* subplots that are to be produced. It calls
`pt.set_xlabel("X")` to make the x-axis label "X" and calls
`pt.set_grid()` to include a grid, for all subplots.

Then the example code does a context call on the `pt` object to obtain
a contextualized instance of it. Everything done to this
contextualized instance applies to just one subplot rather than all
subplots. So, when the example calls `p.set_ylabel` with a
string-formatted argument, it sets the y-axis label of just one
subplot at a time, based on the value of `funcName`.

The actual subplotting is done with a call to the `p` context
object. The first argument is the x-axis vector `X`, and all
arguments that follow are y-axis vectors plotted against the x-axis
vector. In the example, there's just one y-axis vector, `Y`.

Once the `p` object has been called, the context switches to the next
subplot. In the example, there are two subplots, one above the
other. The second iteration of the `for` loop sets the second
subplot's y-axis label to "cos" and plots a cosine.

### License

Copyright (C) 2017-2018 by Edwin A. Suominen,
<http://edsuom.com/>:

    See edsuom.com for API documentation as well as information about
    Ed's background and other projects, software and otherwise.
    
    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the
    License. You may obtain a copy of the License at
    
      http://www.apache.org/licenses/LICENSE-2.0
    
    Unless required by applicable law or agreed to in writing,
    software distributed under the License is distributed on an "AS
    IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
    express or implied. See the License for the specific language
    governing permissions and limitations under the License.
