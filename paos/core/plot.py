import numpy as np
from matplotlib import pyplot as plt
from matplotlib import ticker as ticks
from matplotlib.patches import Circle, Ellipse, Rectangle
from scipy.special import j1

from paos import logger


def do_legend(axis, ncol=1):
    """
    Create a nice legend for the plots

    Parameters
    ----------
    axis: :class:`~matplotlib.axes.Axes`
        An instance of matplotlib axis
    ncol: int
        The number of legend columns

    Returns
    -------
    out: None
        Produces a nice matplotlib legend

    """
    legend = axis.legend(loc="best", ncol=ncol, frameon=True, prop={"size": 12})
    legend.get_frame().set_facecolor("white")
    legend.get_frame().set_edgecolor("white")
    legend.get_frame().set_alpha(0.8)
    return


def simple_plot(
    fig,
    axis,
    key,
    item,
    ima_scale,
    origin="lower",
    cmap="viridis",
    options={},
):
    """
    Given the POP simulation output dict, plots the squared amplitude of the
    wavefront at the given optical surface.

    Parameters
    ----------
    fig: :class:`~matplotlib.figure.Figure`
        instance of matplotlib figure artist
    axis: :class:`~matplotlib.axes.Axes`
        instance of matplotlib axes artist
    key: int
        optical surface index
    item: dict
        optical surface dict
    ima_scale: str
        plot color map scale, can be either 'linear' or 'log'
    origin: str
        matplotlib plot origin. Defaults to 'lower'
    cmap: str
        matplotlib plot color map. Defaults to 'viridis'
    options: dict
        dictionary containing the options to override the plotting default for one or more surfaces, specified by the
        dictionary key. Available options are the surface scale, an option to display physical units, the surface
        zoom(out), the plot scale and whether to plot dark rings in correspondance to the zeros of the Airy diffraction
        pattern.
        Examples:
        0) options={4: {'ima_scale':'linear'}}
        1) options={4: {'surface_scale':60, 'ima_scale':'linear'}}
        2) options={4: {'surface_scale':21, 'pixel_units':True, 'ima_scale':'linear'}}
        3) options={4: {'surface_zoom':2, 'ima_scale':'log', 'dark_rings': False}}

    Returns
    -------
    None
        updates the :class:`~matplotlib.figure.Figure` object

    Examples
    --------

    >>> from paos.core.parseConfig import parse_config
    >>> from paos.core.run import run
    >>> from paos.core.plot import simple_plot
    >>> pup_diameter, parameters, wavelengths, fields, opt_chains = parse_config('path/to/ini/file')
    >>> ret_val = run(pup_diameter, 1.0e-6 * wavelengths[0], parameters['grid size'],
    >>>              parameters['zoom'], fields[0], opt_chains[0])
    >>> from matplotlib import pyplot as plt
    >>> fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(8, 8))
    >>> key = list(ret_val.keys())[-1]  # plot at last optical surface
    >>> item = ret_val[key]
    >>> simple_plot(fig, ax, key=key, item=item, ima_scale='log')
    >>> plt.show()

    """
    ap, wx, wy = None, None, None
    logger.trace(f"plotting S{key:02d}")

    if key in options.keys() and "pixel_units" in options[key].keys():
        assert isinstance(
            options[key]["pixel_units"], bool
        ), "pixel_units must be boolean"
        pixel_units = options[key]["pixel_units"]
    else:
        pixel_units = False

    if key in options.keys() and "dark_rings" in options[key].keys():
        assert isinstance(
            options[key]["dark_rings"], bool
        ), "dark_rings must be boolean"
        dark_rings = options[key]["dark_rings"]
    else:
        dark_rings = True

    if item["wz"] < 0.005:
        # Use microns
        scale = 1.0e6
        unit = "micron"
    else:
        # Use mm
        scale = 1.0e3
        unit = "mm"

    if "psf" in item.keys():
        ima = np.ma.masked_array(data=item["psf"], mask=item["amplitude"] <= 0.0)
    else:
        ima = np.ma.masked_array(
            data=item["amplitude"] ** 2, mask=item["amplitude"] <= 0.0
        )
    power = ima.sum()

    if key in options.keys() and "ima_scale" in options[key].keys():
        assert isinstance(options[key]["ima_scale"], str), "ima_scale must be a str"
        assert options[key]["ima_scale"] in [
            "linear",
            "log",
        ], "ima_scale can be either linear or log"
        ima_scale = options[key]["ima_scale"]

    if ima_scale == "log":
        ima /= ima.max()
        im = axis.imshow(
            10 * np.ma.log10(ima),
            origin=origin,
            vmin=-20,
            vmax=0,
            cmap=plt.get_cmap(cmap),
        )
        cbar_label = "power/pix [db]"
    elif ima_scale == "linear":
        im = axis.imshow(ima, origin=origin, cmap=plt.get_cmap(cmap))
        cbar_label = "power/pix"
    else:
        logger.error("ima_scale shall be either log or linear")
        raise KeyError("ima_scale shall be either log or linear")

    # cax = make_axes_locatable(axis).append_axes("right", size="5%", pad=0.05)
    # cbar = fig.colorbar(im, cax=cax, orientation="vertical")
    # cbar.set_label(cbar_label)
    fig.colorbar(im, ax=axis, orientation="vertical", label=cbar_label)

    if item["aperture"] is not None:
        x, y = item["aperture"].positions
        dx = 1.0 / scale if pixel_units else item["dx"]
        dy = 1.0 / scale if pixel_units else item["dy"]
        shapex = item["wfo"].shape[1]
        shapey = item["wfo"].shape[0]
        xy = scale * (x - shapex // 2) * dx, scale * (y - shapey // 2) * dy

        if hasattr(item["aperture"], "w") and hasattr(item["aperture"], "h"):
            w = item["aperture"].w
            h = item["aperture"].h
            wx = w * dx * scale
            wy = h * dy * scale
            xy = xy[0] - wx / 2, xy[1] - wy / 2
            ap = Rectangle(xy, wx, wy, ec="r", lw=5, fill=False)

        elif hasattr(item["aperture"], "a") and hasattr(item["aperture"], "b"):
            a = item["aperture"].a
            b = item["aperture"].b
            wx = 2 * a * dx * scale
            wy = 2 * b * dy * scale
            ap = Ellipse(xy, wx, wy, ec="r", lw=5, fill=False)

        axis.add_patch(ap)

    im.set_extent(np.array(item["extent"]) * scale)

    beam_radius = scale * item["wz"]
    airy_radius = 1.22 * scale * item["fratio"] * item["wl"]

    if np.isfinite(airy_radius) and dark_rings:
        for airy_scale in [1.22, 2.23, 3.24, 4.24, 5.24]:
            arad = airy_radius * airy_scale / 1.22
            width = 2.0 * arad / (scale * item["dx"]) if pixel_units else 2.0 * arad
            height = 2.0 * arad / (scale * item["dy"]) if pixel_units else 2.0 * arad
            aper = Ellipse(
                (0, 0),
                width=width,
                height=height,
                ec="k",
                lw=5,
                fill=False,
                alpha=0.5,
            )
            axis.add_patch(aper)

    if (
        beam_radius < airy_radius
        and (item["ABCDt"]() != np.eye(2)).all()
        and np.isfinite(airy_radius)
    ):
        plot_scale = 5.24 * airy_radius / 1.22  # 5th Airy null
    elif item["aperture"] is not None:
        plot_scale = max(wx / 2, wy / 2)
    else:
        plot_scale = beam_radius

    if key in options.keys():
        if "surface_zoom" in options[key].keys():
            plot_scale *= options[key]["surface_zoom"]
        elif "surface_scale" in options[key].keys():
            plot_scale = options[key]["surface_scale"]

    axis.set_title(
        rf"S{key:02d}"
        + "\n"
        + rf"F\#{item['fratio']:.2f} | w{scale * item['wz']:.2f}{unit:s} | "
        rf"$\lambda${1.0e6 * item['wl']:3.2f}\textmu m | P{100 * power:2.0f}\%",
        y=1.01,
    )

    if pixel_units:
        im.set_extent(
            np.array(item["extent"])
            / np.array([item["dx"], item["dx"], item["dy"], item["dy"]])
        )
        unit = "pixel"

    axis.set_xlabel(unit)
    axis.set_ylabel(unit)
    axis.set_xlim(-plot_scale, plot_scale)
    axis.set_ylim(-plot_scale, plot_scale)
    axis.grid()

    return


def plot_pop(retval, ima_scale="log", ncols=2, figname=None, options={}):
    """
    Given the POP simulation output dict, plots the squared amplitude of the
    wavefront at all the optical surfaces.

    Parameters
    ----------
    retval: dict
        simulation output dictionary
    ima_scale: str
        plot color map scale, can be either 'linear' or 'log'
    ncols: int
        number of columns for the subplots
    figname: str
        name of figure to save
    options: dict
        dict containing the options to display the plot: axis scale, axis unit, zoom scale and color scale.
        Examples:
        0) options={4: {'ima_scale':'linear'}}
        1) options={4: {'surface_scale':60, 'ima_scale':'linear'}}
        2) options={4: {'surface_scale':21, 'pixel_units':True, 'ima_scale':'linear'}}
        3) options={4: {'surface_zoom':2, 'ima_scale':'log'}}


    Returns
    -------
    out: None
        displays the plot output or stores it to the indicated plot path

    Examples
    --------

    >>> from paos.core.parseConfig import parse_config
    >>> from paos.core.run import run
    >>> from paos.core.plot import plot_pop
    >>> pup_diameter, parameters, wavelengths, fields, opt_chains = parse_config('path/to/ini/file')
    >>> ret_val = run(pup_diameter, 1.0e-6 * wavelengths[0], parameters['grid size'],
    >>>              parameters['zoom'], fields[0], opt_chains[0])
    >>> plot_pop(ret_val, ima_scale='log', ncols=3, figname='path/to/output/plot')

    """

    i, j = None, None

    n_subplots = len(retval)
    if ncols > n_subplots:
        ncols = n_subplots

    nrows = n_subplots // ncols
    if n_subplots % ncols:
        nrows += 1

    figsize = (8 * ncols, 6 * nrows)
    fig, ax = plt.subplots(nrows=nrows, ncols=ncols, figsize=figsize)
    fig.patch.set_facecolor("white")
    plt.subplots_adjust(hspace=0.3, wspace=0.5)

    for k, (key, item) in enumerate(retval.items()):

        if n_subplots == 1:
            axis = ax
        elif n_subplots <= ncols:
            axis = ax[k]
        else:
            i = k % ncols
            j = k // ncols
            axis = ax[j, i]

        simple_plot(
            fig=fig,
            axis=axis,
            key=key,
            item=item,
            ima_scale=ima_scale,
            options=options,
        )

        if n_subplots % ncols and k == n_subplots - 1:
            for col in range(i + 1, ncols):
                ax[j, col].set_visible(False)

    if figname is not None:
        fig.savefig(figname, bbox_inches="tight", dpi=150)
        plt.close()
    else:
        fig.tight_layout()
        plt.show()

    return


def plot_psf_xsec(
    fig,
    axis,
    key,
    item,
    ima_scale="linear",
    x_units="standard",
    surface_zoom=1,
):
    """
    Given the POP simulation output dict, plots the cross-sections of the squared amplitude of the
    wavefront at the given optical surface.

    Parameters
    ----------
    fig: :class:`~matplotlib.figure.Figure`
        instance of matplotlib figure artist
    key: int
        optical surface index
    item: dict
        optical surface dict
    ima_scale: str
        y axis scale, can be either 'linear' or 'log'
    x_units: str
        units for x axis. Default is 'standard', to have units of mm or microns.
        Can also be 'wave', i.e. :math:`\\textrm{Displacement} / (F_{num} \\lambda)`.
    surface_zoom: scalar
        Surface zoom: more increases the axis limits

    Returns
    -------
    out: None
        updates the `~matplotlib.figure.Figure` object
    Examples
    --------

    >>> import matplotlib.pyplot as plt
    >>> from paos.core.parseConfig import parse_config
    >>> from paos.core.run import run
    >>> from paos.core.plot import plot_psf_xsec
    >>> pup_diameter, parameters, wavelengths, fields, opt_chains = parse_config('/path/to/config/file')
    >>> wl_idx = 0  # choose the first wavelength
    >>> wavelength, opt_chain = wavelengths[wl_idx], opt_chains[wl_idx]
    >>> ret_val = run(pup_diameter, 1.0e-6 * wavelength, parameters['grid_size'], parameters['zoom'],
    >>>               fields[0], opt_chain)
    >>> key = list(ret_val.keys())[-1]  # plot at last optical surface
    >>> fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(16, 8))
    >>> plot_psf_xsec(fig=fig,axis=ax,key=key,item=ret_val[key],ima_scale='log',x_units='wave')

    """

    logger.trace("plotting S{:02d}".format(key))

    wx, wy = None, None

    if item["wz"] < 0.005:
        # Use microns
        scale = 1.0e6
        unit = "micron"
    else:
        # Use mm
        scale = 1.0e3
        unit = "mm"

    if "psf" in item.keys():
        ima = np.ma.masked_array(data=item["psf"], mask=item["amplitude"] <= 0.0)
    else:
        ima = np.ma.masked_array(
            data=item["amplitude"] ** 2, mask=item["amplitude"] <= 0.0
        )
    power = ima.sum()

    Npt = ima.shape[0]
    cross_idx = range(ima.shape[0])

    airy_radius = 1.22 * item["fratio"] * item["wl"] * scale
    dx, dy = item["dx"], item["dy"]

    if item["aperture"] is not None:

        if hasattr(item["aperture"], "w") and hasattr(item["aperture"], "h"):
            w = item["aperture"].w
            h = item["aperture"].h
            wx = w * dx * scale
            wy = h * dy * scale

        elif hasattr(item["aperture"], "a") and hasattr(item["aperture"], "b"):
            a = item["aperture"].a
            b = item["aperture"].b
            wx = 2 * a * dx * scale
            wy = 2 * b * dy * scale

    beam_radius = scale * item["wz"]
    if (
        beam_radius < airy_radius
        and (item["ABCDt"]() != np.eye(2)).all()
        and np.isfinite(airy_radius)
    ):
        plot_scale = 5.24 * airy_radius / 1.22  # 5th Airy null
    elif item["aperture"] is not None:
        plot_scale = max(wx / 2, wy / 2)
    else:
        plot_scale = beam_radius
    x_label = unit

    # Build the axis arrays
    airy_scale = 1.22 / airy_radius
    x_i = dx * scale * np.linspace(-Npt // 2, Npt // 2, Npt, endpoint=False)
    y_i = x_i * dy / dx

    if item["wz"] < 0.005:

        # Rescale the axis arrays
        x_i *= airy_scale
        y_i *= airy_scale

        # Airy 2D function, normalised to area 1
        xx, yy = np.meshgrid(x_i, y_i)
        r = np.pi * np.sqrt(xx**2 + yy**2) + 1.0e-30
        airy = (2.0 * j1(r) / r) ** 2
        normalization = 0.25 * np.pi * (x_i[1] - x_i[0]) * (y_i[1] - y_i[0])
        airy *= normalization

        if x_units == "standard":
            plot_scale = 5.24 / airy_scale
            x_i /= airy_scale
            y_i /= airy_scale

        if x_units == "wave":
            airy_scale = 1.0
            plot_scale = 5.24
            x_label = r"1 /F$\lambda$"

        # Plot Airy X and Y cross-sections
        axis.plot(
            x_i, airy[Npt // 2, ...], color="C4", label="Airy X-cut", linestyle="--"
        )
        axis.plot(
            y_i, airy[..., Npt // 2], color="C5", label="Airy Y-cut", linestyle="--"
        )
        axis.set_ylim(1.0e-10, airy.max())

        # plot vertical lines to mark the positions of the Airy dark rings and set the axis ticks
        x_ticks = (
            np.array(
                [
                    -5.24,
                    -4.24,
                    -3.24,
                    -2.23,
                    -1.22,
                    1.22,
                    2.23,
                    3.24,
                    4.24,
                    5.24,
                ]
            )
            / airy_scale
        )
        if surface_zoom <= 1.2:
            axis.vlines(x_ticks, *axis.get_ylim(), colors="k", lw=2, alpha=0.5)
            axis.set_xticks(list(x_ticks) + [0.0])

    # Plot ima X, Y, 45 deg and 135 deg cross-sections
    axis.plot(x_i, ima[Npt // 2, ...], "C0", label="X-cut")
    axis.plot(y_i, ima[..., Npt // 2], "C1", label="Y-cut")

    c = np.sqrt(x_i**2 + y_i**2) * np.sign(x_i)
    axis.plot(
        c,
        ima[cross_idx, cross_idx],
        "C2",
        label=r"45$^\circ$-cut",
    )
    axis.plot(
        c + 0.5 * np.sqrt((x_i[1] - x_i[0]) * (y_i[1] - y_i[0])),
        ima[cross_idx, cross_idx[::-1]],
        "C3",
        label=r"135$^\circ$-cut",
    )

    axis.set_title(
        rf"S{key:02d}"
        + "\n"
        + rf"F\#{item['fratio']:.2f} | w{scale * item['wz']:.2f}{unit:s} | "
        rf"$\lambda${1.0e6 * item['wl']:3.2f}\textmu m | P{100 * power:2.0f}\%",
        y=1.01,
    )

    axis.set_ylabel("Cross-sections")
    axis.set_xlabel(x_label)
    axis.get_xaxis().set_major_formatter(ticks.ScalarFormatter())
    axis.tick_params(labelrotation=45)
    axis.set_yscale(ima_scale)
    axis.set_xlim(-plot_scale * surface_zoom, plot_scale * surface_zoom)

    do_legend(axis=axis, ncol=3 if item["wz"] < 0.005 else 2)
    axis.grid()

    return


def plot_surface(key, retval, ima_scale, origin="lower", zoom=1, figname=None):
    """
    Given the optical surface key, the POP output dictionary and the image scale, plots the squared amplitude
    of the wavefront at the given surface (cross-sections and 2D plot)

    Parameters
    ----------
    key: int
        the key index associated to the optical surface
    retval: dict
        the POP output dictionary
    ima_scale: str
        the image scale. Can be either 'linear' or 'log'
    origin: str
        matplotlib plot origin. Defaults to 'lower'
    zoom: scalar
        the surface zoom factor: more increases the axis limits
    figname: str
        name of figure to save

    Returns
    -------
    out: :class:`~matplotlib.figure.Figure`
        the figure with the squared amplitude of the wavefront at the given surface

    """

    fig, axs = plt.subplots(nrows=1, ncols=2, figsize=(12, 6))
    # Xsec plot
    plot_psf_xsec(
        fig=fig,
        axis=axs[0],
        key=key,
        item=retval[key],
        ima_scale=ima_scale,
        surface_zoom=zoom,
    )
    # 2D plot
    simple_plot(
        fig=fig,
        axis=axs[1],
        key=key,
        item=retval[key],
        ima_scale=ima_scale,
        origin=origin,
        options={key: {"surface_zoom": zoom}},
    )
    fig.suptitle(axs[0].get_title(), fontsize=20)
    axs[0].set_title("X-sec view")
    axs[1].set_title("2D view")
    fig.tight_layout()

    if figname is not None:
        fig.savefig(figname, bbox_inches="tight", dpi=150)
        plt.close()

    return fig
