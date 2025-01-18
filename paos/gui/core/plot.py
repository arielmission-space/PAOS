import numpy as np
import matplotlib.pyplot as plt


def wfe_plot(
    fig,
    axis,
    surface,
    item,
    title,
):

    if item["wz"] < 0.005:
        # Use microns
        scale = 1.0e6
        unit = r"\textmu m"
    else:
        # Use mm
        scale = 1.0e3
        unit = "mm"

    plot_scale = item["wz"] * scale

    im = axis.imshow(item["wfe"], origin="lower", cmap=plt.get_cmap("viridis"))
    im.set_extent(np.array(item["extent"]) * scale)

    fig.colorbar(im, ax=axis, orientation="vertical", label="WFE [m]")

    axis.set_title(f"{surface}" + "\n" + title, y=1.05)
    axis.set_xlabel(unit)
    axis.set_ylabel(unit)
    axis.set_xlim(-plot_scale, plot_scale)
    axis.set_ylim(-plot_scale, plot_scale)
    axis.grid()

    return
