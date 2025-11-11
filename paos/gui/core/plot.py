import matplotlib.pyplot as plt
import numpy as np


def wfe_plot(
    fig,
    axis,
    surface,
    item,
    title,
    zoom,
):

    if item["wz"] < 0.005:
        # Use microns
        scale = 1.0e6
        unit = r"\textmu m"
    else:
        # Use mm
        scale = 1.0e3
        unit = "mm"

    extent = np.array(item["extent"]) * scale

    im = axis.imshow(item["wfe"], origin="lower", cmap=plt.get_cmap("viridis"))
    im.set_extent(extent)

    fig.colorbar(im, ax=axis, orientation="vertical", label="WFE [m]")

    axis.set_title(f"{surface}" + "\n" + title, y=1.05)
    axis.set_xlabel(unit)
    axis.set_ylabel(unit)
    axis.set_xlim(extent[0] / zoom, extent[1] / zoom)
    axis.set_ylim(extent[2] / zoom, extent[3] / zoom)
    axis.grid()

    return
