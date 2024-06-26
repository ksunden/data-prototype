"""
===========================================
Using pint units with PathCollectionWrapper
===========================================

Using third party units functionality in conjunction with Matplotlib Axes
"""

import numpy as np
from collections import defaultdict

import matplotlib.pyplot as plt
import matplotlib.markers as mmarkers

from data_prototype.artist import CompatibilityAxes
from data_prototype.containers import ArrayContainer
from data_prototype.conversion_edge import FuncEdge
from data_prototype.description import Desc

from data_prototype.line import Line

import pint

ureg = pint.UnitRegistry()
ureg.setup_matplotlib()

marker_obj = mmarkers.MarkerStyle("o")


coords = defaultdict(lambda: "auto")
coords["x"] = coords["y"] = "units"
cont = ArrayContainer(
    coords,
    x=np.array([0, 1, 2]) * ureg.m,
    y=np.array([1, 4, 2]) * ureg.m,
    paths=np.array([marker_obj.get_path()]),
    sizes=np.array([12]),
    edgecolors=np.array(["k"]),
    facecolors=np.array(["C3"]),
)

fig, nax = plt.subplots()
ax = CompatibilityAxes(nax)
nax.add_artist(ax)
ax.set_xlim(-0.5, 7)
ax.set_ylim(0, 5)

scalar = Desc((), "units")
unit_vector = Desc(("N",), "units")

xconv = FuncEdge.from_func(
    "xconv",
    lambda x, xunits: x.to(xunits),
    {"x": unit_vector, "xunits": scalar},
    {"x": Desc(("N",), "data")},
)
yconv = FuncEdge.from_func(
    "yconv",
    lambda y, yunits: y.to(yunits),
    {"y": unit_vector, "yunits": scalar},
    {"y": Desc(("N",), "data")},
)
lw = Line(cont, [xconv, yconv])

ax.add_artist(lw)
nax.xaxis.set_units(ureg.m)
nax.yaxis.set_units(ureg.cm)

plt.show()
