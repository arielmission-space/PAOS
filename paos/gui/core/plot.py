import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Ellipse

from paos import Zernike, PolyOrthoNorm

from paos import logger


plt.rcParams["figure.facecolor"] = "white"
plt.rc("lines", linewidth=1.5)
plt.rc(
    "axes",
    axisbelow=True,
    titleweight="bold",
    labelcolor="dimgray",
    labelweight="bold",
)
plt.rc("font", size=12)
plt.rc("text", usetex=True)


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
        unit = r"\textmu m"
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
        print("ima_scale shall be either log or linear")
        raise KeyError("ima_scale shall be either log or linear")

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
        y=1.05,
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


def zernike_plot(
    fig, axis, surface, index, Z, wavelength, ordering, normalize, orthonorm, grid_size
):
    x = np.linspace(-1.0, 1.0, grid_size)
    xx, yy = np.meshgrid(x, x)
    rho = np.sqrt(xx**2 + yy**2)
    phi = np.arctan2(yy, xx)
    wavelength *= 1.0e-6  # convert to meters
    Z = np.array(Z) * wavelength

    func = PolyOrthoNorm if orthonorm else Zernike
    logger.debug(f"Using {func.__name__} polynomials")

    zernike = func(len(index), rho, phi, ordering=ordering, normalize=normalize)
    zer = zernike()
    wfe = (zer.T * Z).T.sum(axis=0)
    logger.debug(f"WFE RMS = {np.std(wfe)}")

    im = axis.imshow(wfe, origin="lower", cmap=plt.get_cmap("viridis"))
    fig.colorbar(im, ax=axis, orientation="vertical", label="WFE [m]")

    axis.set_title(
        f"{surface}" + "\n" + "Zernike errormap",
        y=1.05,
    )
    axis.set_xlabel("pix")
    axis.set_ylabel("pix")
    axis.grid()

    return
