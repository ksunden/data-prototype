import numpy as np


import matplotlib as mpl
from data_prototype.artist import CompatibilityAxes
from matplotlib.axes._axes import Axes as MPLAxes, _preprocess_data
from matplotlib.axes._base import _process_plot_var_args
import matplotlib.collections as mcoll
import matplotlib.cbook as cbook
import matplotlib.lines as mlines
import matplotlib.markers as mmarkers
import matplotlib.projections as mprojections

from .containers import ArrayContainer, DataUnion
from .conversion_node import (
    DelayedConversionNode,
    FunctionConversionNode,
    RenameConversionNode,
)
from .line import Line
from .wrappers import PathCollectionWrapper


class Axes(MPLAxes):
    # Name for registering as a projection so we can experiment with it
    name = "data-prototype"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ca = CompatibilityAxes(self)
        self._get_lines_mirror = _process_plot_var_args("mirror")
        self.add_artist(self._ca)

    @_preprocess_data(
        replace_names=[
            "x",
            "y",
            "s",
            "linewidths",
            "edgecolors",
            "c",
            "facecolor",
            "facecolors",
            "color",
        ],
        label_namer="y",
    )
    def scatter(
        self,
        x,
        y,
        s=None,
        c=None,
        marker=None,
        cmap=None,
        norm=None,
        vmin=None,
        vmax=None,
        alpha=None,
        linewidths=None,
        *,
        edgecolors=None,
        plotnonfinite=False,
        **kwargs
    ):
        # TODO implement normalize kwargs as a pipeline stage
        # add edgecolors and linewidths to kwargs so they can be processed by
        # normalize_kwargs
        if edgecolors is not None:
            kwargs.update({"edgecolors": edgecolors})
        if linewidths is not None:
            kwargs.update({"linewidths": linewidths})

        kwargs = cbook.normalize_kwargs(kwargs, mcoll.Collection)
        c, colors, edgecolors = self._parse_scatter_color_args(
            c,
            edgecolors,
            kwargs,
            np.ma.ravel(x).size,
            get_next_color_func=self._get_patches_for_fill.get_next_color,
        )

        inputs = ArrayContainer(
            x=x,
            y=y,
            s=s,
            c=c,
            marker=marker,
            cmap=cmap,
            norm=norm,
            vmin=vmin,
            vmax=vmax,
            alpha=alpha,
            plotnonfinite=plotnonfinite,
            facecolors=colors,
            edgecolors=edgecolors,
            **kwargs
        )
        # TODO should more go in here?
        # marker/s are always in Container, but require overriding if None
        # Color handling is odd too
        defaults = ArrayContainer(
            linewidths=mpl.rcParams["lines.linewidth"],
        )

        cont = DataUnion(defaults, inputs)

        pipeline = []
        xconvert = DelayedConversionNode.from_keys(("x",), converter_key="xunits")
        yconvert = DelayedConversionNode.from_keys(("y",), converter_key="yunits")
        pipeline.extend([xconvert, yconvert])
        pipeline.append(lambda x: np.ma.ravel(x))
        pipeline.append(lambda y: np.ma.ravel(y))
        pipeline.append(
            lambda s: (
                np.ma.ravel(s)
                if s is not None
                else (
                    [20]
                    if mpl.rcParams["_internal.classic_mode"]
                    else [mpl.rcParams["lines.markersize"] ** 2.0]
                )
            )
        )
        # TODO plotnonfinite/mask combining
        pipeline.append(
            lambda marker: (
                marker if marker is not None else mpl.rcParams["scatter.marker"]
            )
        )
        pipeline.append(
            lambda marker: (
                marker
                if isinstance(marker, mmarkers.MarkerStyle)
                else mmarkers.MarkerStyle(marker)
            )
        )
        pipeline.append(
            FunctionConversionNode.from_funcs(
                {
                    "paths": lambda marker: [
                        marker.get_path().transformed(marker.get_transform())
                    ]
                }
            )
        )
        pipeline.append(RenameConversionNode.from_mapping({"s": "sizes"}))

        # TODO classic mode margin override?
        pcw = PathCollectionWrapper(cont, pipeline, offset_transform=self.transData)
        self.add_artist(pcw)
        self._request_autoscale_view()
        return pcw

    def plot(self, *args, scalex=True, scaley=True, data=None, **kwargs):
        kwargs = cbook.normalize_kwargs(kwargs, mlines.Line2D)
        line_args = [*self._get_lines_mirror(self, *args, data=data, **kwargs)]
        print(line_args)
        lines = []
        for coord, kws in line_args:
            cont = ArrayContainer(**{"x": coord[0], "y": coord[1]})
            line = Line(cont, **kws)
            lines.append(line)
            self._ca.add_artist(line)
        if scalex:
            self._request_autoscale_view("x")
        if scaley:
            self._request_autoscale_view("y")
        return lines


# This is a handy trick to allow e.g. plt.subplots(subplot_kw={'projection': 'data-prototype'})
mprojections.register_projection(Axes)
