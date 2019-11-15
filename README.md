## yampex
*Yet Another Matplotlib Extension, with simplified subplotting*

* [API Docs](http://edsuom.com/yampex/yampex.html)
* [PyPI Page](https://pypi.python.org/pypi/yampex/)
* [Project Page](http://edsuom.com/yampex.html) at **edsuom.com**

*yampex* makes Matplotlib easier to use, especially with subplots and
annotations. You simply construct a `Plotter` object with the number
of subplot rows and columns you want, and do a context call on it to
get a version of the object that's all set up to do your
subplots. Like this:

    import numpy as np
    from yampex import Plotter
    
    funcNames = ('sin', 'cos')
    X = np.linspace(0, 4*np.pi, 200)
    pt = Plotter(1, 2, width=7, height=5)
    pt.set_xlabel("X"); pt.set_grid()
    with pt as p:
        for funcName in funcNames:
            Y = getattr(np, funcName)(X)
            p.set_ylabel("{}(X)".format(funcName))
            p(X, Y)
    pt.show()

The `Plotter` instance `pt` has various methods for setting plot
modes. The example calls two of them before it makes the context call,
thus affecting *all* subplots that are to be produced. It calls
`pt.set_xlabel("X")` to make the x-axis label "X" and calls
`pt.set_grid()` to include a grid, for all subplots.

Then the example code does a context call on the `pt` object to obtain
a contextualized instance of it, `p`. Everything done to this
contextualized instance applies to just one subplot rather than all
subplots. So, when the example calls `p.set_ylabel` with a
string-formatted argument, it sets the y-axis label of just one
subplot at a time, based on the value of `funcName`.

The actual subplotting is done with a call to the `p` context object
itself (not a method of it). The first argument is the x-axis vector
`X`, and all arguments that follow are y-axis vectors plotted against
the x-axis vector. In the example, there's just one y-axis vector,
`Y`. You can supply additional vectors to be plotted against the first
x-axis one and they will show up in different colors.

Once the `p` object has been called, the context switches to the next
subplot. In the example, there are two subplots, one above the
other. The second iteration of the `for` loop sets the second
subplot's y-axis label to "cos" and plots a cosine.

![result](http://edsuom.com/yampex-example.png)


### Annotations

Another thing that *yampex* can do for you is to annotate your plots
with intelligently-positioned labels. You don't have to worry about
whether your annotation graphic will obscure part of the plot line, or
sit on top of the plot borders looking ugly and weird. And adding the
annotations is as simple as calling the `add_annotation` method of
your plotter object. You make the call outside the *with-as* context
if you want to add the annotation to all subplots, or in context to
affect just one subplot.

Let's expand the example to add annotations to the sine and cosine
curves.

    import numpy as np
    from yampex import Plotter

    funcNames = ('sin', 'cos')
    X = np.linspace(0, 4*np.pi, 200)
    pt = Plotter(1, 2, width=7, height=5)
    pt.set_title("Sin and Cosine")
    pt.set_xlabel("X"); pt.set_grid()
    pt.add_annotation(199, "Last")
    with pt as p:
        for funcName in funcNames:
            Y = getattr(np, funcName)(X)
            p.set_ylabel("{}(X)".format(funcName))
            k = 0 if funcName == 'sin' else 75
            for text in ("Pos ZC", "Max", "Neg ZC", "Min"):
                p.add_annotation(k, text)
                k += 25
            p.set_axvline(k)
            p(X, Y)
    pt.show()

First we add a global annotation to the overall Matplotlib-manager
object `pt` that affects all subplots; the last point plotted is
labeled "Last."  Then we enter the context manager and, via the
contextualized object `p`, add annotations to each subplot for a
positive zero crossing. The annotations are a maximum, a negative zero
crossing, and a minimum.

![with annotations](http://edsuom.com/yampex-example-annotated.png)

Note how the annotation boxes are positioned so that they don't cover
up the plots or each other, or trespass on the borders. A surprisingly
large amount of thought and computation went into making that
happen. If you're interested, you can check out the
[gory details](http://edsuom.com/yampex/annotate.py.html) of the
`Annotator` class and its `Sizer`, `Rectangle`, and `Positioner`
helpers.

A couple of other things you might notice: There's a dashed vertical
line at the zero crossing after the last annotation. That was added by
calling `p.set_axvline(k)`. Take a look at the methods of
[OptsBase](http://edsuom.com/yampex/yampex.plot.OptsBase.html) to see
all the options you can set. Another one that the example code has set
(on a global scale, before entering the context manager) was the title
for all subplots. You could just as easily set a different title for
each subplot inside the context manager.

### License

Copyright (C) 2017-2019 by Edwin A. Suominen,
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
