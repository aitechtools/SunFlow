<img width="2074" alt="SunFlow Image" src="https://user-images.githubusercontent.com/65407412/84622752-0c445900-aede-11ea-8ce4-903da112db65.png">

# Design & Optimize your Supply Chain

SunFlow is a tool to design and optimize your Supply Chains. In SunFlow a supply model is made of materials, components, parts, products, substitutes, suppliers, manufacturers, distributors and customers - just to mention the major ones - together with fix and variable costs, capacities and other constraints. With SunFlow you model all kinds of industrial supply chains from simple transportation networks up to complex multi-level manufacturing setups.

Tutorials
---------

Illustrative tutorials explain SunFlow's capabilities and their usage by Python examples step-by-step. Their source code is inside the examples folder.

Powerful Graphics
-----------------

SunFlow got powerful graphics. Your network can be displayed at any time. Have a look on the artificial and schematic assembly of a Porsche Taycan electric as an example. First you graph the network with all potential connections and definitions for cost, freight, capacities, products, components, suppliers, plants, distribution centers and customers or markets.

<img width="977" alt="Taycan Graph" src="https://user-images.githubusercontent.com/65407412/84750084-22741700-afbb-11ea-97f2-b9e38b627480.png">

Once you got the network, you execute the potential flows to identify the cost-optimal flow, i.e. you optimize it. Our optimized network is shown below.

<img width="996" alt="Taycan Opt" src="https://user-images.githubusercontent.com/65407412/84750108-29028e80-afbb-11ea-85f3-daf695d87633.png">

The optimized model shows active (blue) and inactive flows (gray) as well as active participants (gray boxes) and inactive participants (white boxes). In complex models this could be confusing. This is why SunFlow offers an option to display only those vertices and edge, which have an active flow (see below) in the optimized model.

<img width="1014" alt="Taycan Opt Flow Only" src="https://user-images.githubusercontent.com/65407412/84750118-2dc74280-afbb-11ea-9877-ecbfe2602e4e.png">

Network Compiler
----------------

SunFlow's supply networks are build up in a way Supply Chain Architects think: in terms of components, materials, products, suppliers, plants, assembly lines, reactors, warehouses, distribution centers, customers, markets,...  The above shown illustrations are made by the Python example below.

<img width="978" alt="Taycan Code" src="https://user-images.githubusercontent.com/65407412/84750127-328bf680-afbb-11ea-86bd-14d12103838c.png">

Library
-------

SunFlow's library 'sunflow.py' is in the folder 'lib' together with an installation guide.

Dependencies
------------

SunFlow supports Python 3.6+

The installation requires [numpy](http://www.numpy.org/), [scipy](http://www.scipy.org/), [pandas](http://pandas.pydata.org/) and [graphviz](https://www.graphviz.org).


Data
----

Some of the examples use data which are inside the folder 'data'.

Installation
------------

To install SunFlow on your computer, press 'Clone or download' on SunFlow's Repository site and choose the 'Download ZIP' option. Then SunFlow will be copied into a folder 'SunFlow' or zip inside your download directory, containing the complete SunFlow repository. To proceed further, read the installation guide of folder 'lib'.

