## yampex
*Yet Another Matplotlib Extension, with simplified subplotting*

* [API Docs](http://edsuom.com/yampex/yampex.html)
* [PyPI Page](https://pypi.python.org/pypi/yampex/)
* [Project Page](http://edsuom.com/yampex.html) at **edsuom.com**

*yampex* makes Matplotlib easier to use, especially with subplots. You
simply construct a `Plotter` object with the number of subplot rows
and columns you want, and do a context call on it to get a version of
the object that's all set up to do your subplots. Like this:

    from yampex import Plotter
    pt = Plotter(1, 2)
    with pt as p:
        for k in (1, 2):
            V = self.ev.txy[:,k]
            I = np.argsort(V)
            V = V[I]
            xName = sub("V{:d}", k)
            ax = self.plot(V, T[I], p, xName)
            t_curve = self.ev.curve_k(values, k)
            ax.plot(V, t_curve[I], 'r-')
    self.pt.figTitle(", ".join(self.titleParts))
    self.pt.show()

    
    



Here's one example, `unique-visitors-by-url-recent.sql`:

    SELECT year(e.dt) YR, month(e.dt) MO, count(distinct e.ip) N, url.value URL
    FROM entries e INNER JOIN vhost ON e.id_vhost = vhost.id
    INNER JOIN url ON e.id_url = url.id
    WHERE vhost.value REGEXP '^(www\.)?edsuom\.com'
     AND e.http != 404
     AND url.value NOT REGEXP '\.(jpg|png|gif|ico|css)'
    GROUP BY URL, YR, MO
    HAVING N > 1
    ORDER BY YR DESC, MO DESC, N DESC;

Obviously, change *edsuom.com* to one of your virtual hosts. This SQL
query will show you how many unique IP addresses were fetching the
most popular URLs on that virtual host, for each year and month.


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
