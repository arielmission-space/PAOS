import numpy as np
from scipy.special import j1
from matplotlib import pyplot as plt
from matplotlib.patches import Ellipse, Circle, Rectangle
from matplotlib import ticker as ticks
from mpl_toolkits.axes_grid1 import make_axes_locatable
from .paos_config import logger


def simple_plot(fig, axis, key, item, ima_scale, options=dict()):
    """
    Given the POP simulation output dict, plots the squared amplitude of the
    wavefront at the given optical surface.

    Parameters
    ----------
    fig: `~matplotlib.figure.Figure`
        instance of matplotlib figure artist
    axis: `~matplotlib.axes.Axes`
        instance of matplotlib axes artist
    key: int
        optical surface index
    item: dict
        optical surface dict
    ima_scale: str
        plot color map scale, can be either 'linear' or 'log'
    options: dict
        dict containing the options to display the plot: axis scale, option to display physical units,
        zoom scale and color scale.
        ex. 0) options={4: {'ima_scale':'linear'}}
            1) options={4: {'surface_scale':60, 'ima_scale':'linear'}}
            2) options={4: {'surface_scale':21, 'pixel_units':True, 'ima_scale':'linear'}}
            3) options={4: {'surface_zoom':2, 'ima_scale':'log'}}

    Returns
    -------
    None or `~matplotlib.figure.Figure`
        displays the plot output or stores it to the indicated plot path

    Examples
    --------

    >>> from paos.paos_parseconfig import parse_config
    >>> from paos.paos_run import run
    >>> from paos.paos_plotpop import simple_plot
    >>> pup_diameter, general, fields, opt_chain = parse_config('path/to/conf/file')
    >>> ret_val = run(pup_diameter, 1.0e-6 * general['wavelength'], general['grid size'],
    >>>              general['zoom'], fields['0'], opt_chain)
    >>> from matplotlib import pyplot as plt
    >>> fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(8, 8))
    >>> key = list(ret_val.keys())[-1]  # plot at last optical surface
    >>> item = ret_val[key]
    >>> simple_plot(fig, ax, key=key, item=item, ima_scale='log')
    >>> plt.show()

    """
    logger.trace('plotting S{:02d}'.format(key))

    if key in options.keys() and 'pixel_units' in options[key].keys():
        assert isinstance(options[key]['pixel_units'], bool), 'pixel_units must be boolean'
        pixel_units = options[key]['pixel_units']
    else:
        pixel_units = False

    if item['wz'] < 0.005:
        # Use microns
        scale = 1.0e6
        unit = 'micron'
    else:
        # Use mm
        scale = 1.0e3
        unit = 'mm'

    if 'psf' in item.keys():
        ima = np.ma.masked_array(data=item['psf'], mask=item['amplitude'] <= 0.0)
    else:
        ima = np.ma.masked_array(data=item['amplitude'] ** 2, mask=item['amplitude'] <= 0.0)
    power = ima.sum()

    if key in options.keys() and 'ima_scale' in options[key].keys():
        assert isinstance(options[key]['ima_scale'], str), "ima_scale must be a str"
        assert options[key]['ima_scale'] in ['linear', 'log'], "ima_scale can be either linear or log"
        ima_scale = options[key]['ima_scale']

    if ima_scale == 'log':
        ima /= ima.max()
        im = axis.imshow(10 * np.ma.log10(ima), origin='lower', vmin=-20, vmax=0)
        cbar_label = 'power/pix [db]'
    elif ima_scale == 'linear':
        im = axis.imshow(ima, origin='lower')
        cbar_label = 'power/pix'
    else:
        logger.error('ima_scale shall be either log or linear')
        raise KeyError('ima_scale shall be either log or linear')

    cax = make_axes_locatable(axis).append_axes('right', size='5%', pad=0.05)
    cbar = fig.colorbar(im, cax=cax, orientation='vertical')
    cbar.set_label(cbar_label)

    if item['aperture'] is not None:
        x, y = item['aperture'].positions
        dx = 1.0 / scale if pixel_units else item['dx']
        dy = 1.0 / scale if pixel_units else item['dy']
        shapex = item['wfo'].shape[1]
        shapey = item['wfo'].shape[0]
        xy = scale * (x - shapex // 2) * dx, scale * (y - shapey // 2) * dy

        if hasattr(item['aperture'], 'w') and hasattr(item['aperture'], 'h'):
            w = item['aperture'].w
            h = item['aperture'].h
            wx = w * dx * scale
            wy = h * dy * scale
            xy = xy[0] - wx / 2, xy[1] - wy / 2
            ap = Rectangle(xy, wx, wy, ec='r', lw=5, fill=False)

        elif hasattr(item['aperture'], 'a') and hasattr(item['aperture'], 'b'):
            a = item['aperture'].a
            b = item['aperture'].b
            wx = 2 * a * dx * scale
            wy = 2 * b * dy * scale
            ap = Ellipse(xy, wx, wy, ec='r', lw=5, fill=False)

        axis.add_patch(ap)

    im.set_extent(np.array(item['extent']) * scale)

    beamradius = scale * item['wz']
    airyradius = 1.22 * scale * item['fratio'] * item['wl']

    if np.isfinite(airyradius):
        for airy_scale in [1.22, 2.23, 3.24, 4.24, 5.24]:
            arad = airyradius * airy_scale / 1.22
            width = 2.0 * arad / (scale * item['dx']) if pixel_units else 2.0 * arad
            height = 2.0 * arad / (scale * item['dy']) if pixel_units else 2.0 * arad
            aper = Ellipse((0, 0), width=width, height=height, ec='k', lw=5, fill=False, alpha=0.5)
            axis.add_patch(aper)

    if beamradius < airyradius and (item['ABCDt']() != np.eye(2)).all() and np.isfinite(airyradius):
        plotscale = 5.24 * airyradius / 1.22  # 5th Airy null
    elif not item['aperture'] is None:
        plotscale = max(wx / 2, wy / 2)
    else:
        plotscale = beamradius

    if key in options.keys():
        if 'surface_zoom' in options[key].keys():
            plotscale *= options[key]['surface_zoom']
        elif 'surface_scale' in options[key].keys():
            plotscale = options[key]['surface_scale']

    axis.set_title(r"S{:02d} | F#{:.2f} | w{:.2f}{:s} | $\lambda${:3.2f}$\mu$m | P{:2.0f}%".format(
        key, item['fratio'], scale * item['wz'], unit, 1.0e6 * item['wl'], 100 * power))

    if pixel_units:
        im.set_extent(np.array(item['extent']) / np.array([item['dx'], item['dx'], item['dy'], item['dy']]))
        unit = 'pixel'

    axis.set_xlabel(unit)
    axis.set_ylabel(unit)
    axis.set_xlim(-plotscale, plotscale)
    axis.set_ylim(-plotscale, plotscale)
    axis.grid()

    return


def plot_pop(retval, ima_scale='log', ncols=2, figname=None, options=dict()):
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
        ex. 0) options={4: {'ima_scale':'linear'}}
            1) options={4: {'surface_scale':60, 'ima_scale':'linear'}}
            2) options={4: {'surface_scale':21, 'pixel_units':True, 'ima_scale':'linear'}}
            3) options={4: {'surface_zoom':2, 'ima_scale':'log'}}


    Returns
    -------
    None
        displays the plot output or stores it to the indicated plot path

    Examples
    --------

    >>> from paos.paos_parseconfig import parse_config
    >>> from paos.paos_run import run
    >>> from paos.paos_plotpop import plot_pop
    >>> pup_diameter, general, fields, opt_chain = parse_config('path/to/conf/file')
    >>> ret_val = run(pup_diameter, 1.0e-6 * general['wavelength'], general['grid size'],
    >>>              general['zoom'], fields['0'], opt_chain)
    >>> plot_pop(ret_val, ima_scale='log', ncols=3, figname='path/to/output/plot')

    """

    n_subplots = len(retval)
    if ncols > n_subplots:
        ncols = n_subplots

    nrows = n_subplots // ncols
    if n_subplots % ncols: nrows += 1

    figsize = (8 * ncols, 6 * nrows)
    fig, ax = plt.subplots(nrows=nrows, ncols=ncols, figsize=figsize)
    fig.patch.set_facecolor('white')
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

        simple_plot(fig, axis, key, item, ima_scale, options)

        if n_subplots % ncols and k == n_subplots - 1:
            for col in range(i + 1, ncols):
                ax[j, col].set_visible(False)

    if figname is not None:
        fig.savefig(figname, bbox_inches='tight', dpi=150)
        plt.close()
    else:
        fig.tight_layout()
        plt.show()

    return


def plot_psf_xsec(fig, axis, key, item, psf_scale='linear', x_units='wave'):
    """
    Given the POP simulation output dict, plots the cross sections of the squared amplitude of the
    wavefront at the given optical surface.

    Parameters
    ----------
    fig: `~matplotlib.figure.Figure`
        instance of matplotlib figure artist
    key: int
        optical surface index
    item: dict
        optical surface dict
    psf_scale: str
        y axis scale, can be either 'linear' or 'log'
    x_units: str
        units for x axis. Default is wave, i.e. :math:`\\textrm{Displacement} / (F_# \\lambda)`.
        Can also be 'standard', to have mm or microns.

    Returns
    -------
    None or `~matplotlib.figure.Figure`
        displays the plot output or stores it to the indicated plot path

    Examples
    --------

    >>> from paos.paos_parseconfig import parse_config
    >>> from paos.paos_run import run
    >>> from paos.paos_plotpop import simple_plot
    >>> pup_diameter, general, fields, opt_chain = parse_config('path/to/conf/file')
    >>> ret_val = run(pup_diameter, 1.0e-6 * general['wavelength'], general['grid size'],
    >>>              general['zoom'], fields['0'], opt_chain)
    >>> key = list(ret_val.keys())[-1]  # plot at last optical surface
    >>> from paos.paos_plotpop import plot_psf_xsec
    >>> fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(8, 8))
    >>> plot_psf_xsec(fig=fig, axis=ax, key=key, item=ret_val[key], x_units='wave')

    """

    logger.trace('plotting S{:02d}'.format(key))

    if item['wz'] < 0.005:
        # Use microns
        scale = 1.0e6
        unit = 'micron'
    else:
        # Use mm
        scale = 1.0e3
        unit = 'mm'

    airyradius = 1.22 * item['fratio'] * item['wl'] * scale

    dx, dy = item['dx'], item['dy']

    if 'psf' in item.keys():
        ima = np.ma.masked_array(data=item['psf'], mask=item['amplitude'] <= 0.0)
    else:
        ima = np.ma.masked_array(data=item['amplitude'] ** 2, mask=item['amplitude'] <= 0.0)
    power = ima.sum()

    Npt = ima.shape[0]
    cross_idx = range(ima.shape[0])
    x_i = dx * scale * np.linspace(-Npt // 2, Npt // 2, Npt, endpoint=False) * 1.22 / airyradius
    y_i = x_i * dy / dx

    # Airy 2D function, normalised to area 1
    xx, yy = np.meshgrid(x_i, y_i)
    r = np.pi * np.sqrt(xx ** 2 + yy ** 2) + 1.0e-30
    airy = (2.0 * j1(r) / r) ** 2
    normalization = 0.25 * np.pi * (x_i[1] - x_i[0]) * (y_i[1] - y_i[0])
    airy *= normalization

    if x_units == 'wave':
        airy_scale = 1.0
        plotscale = 5.24
        xlabel = r'1 /F$\lambda$'
    elif x_units == 'standard':
        airy_scale = 1.22 / airyradius
        x_i, y_i = x_i / airy_scale,  y_i / airy_scale
        xlabel = unit
        plotscale = 5.24 * airyradius / 1.22
    else:
        logger.error('x units not supported. Choose either wave or standard.')

    # Plot
    axis.plot(x_i, ima[Npt // 2, ...], 'r', label='X-cut')
    axis.plot(y_i, ima[..., Npt // 2], 'b', label='Y-cut')
    axis.plot(np.sqrt(x_i ** 2 + y_i ** 2) * np.sign(x_i),
            ima[cross_idx, cross_idx], '--r', label=r'45$^\circ$-cut')
    axis.plot(np.sqrt(x_i ** 2 + y_i ** 2) * np.sign(y_i) + np.sqrt((x_i[1] - x_i[0]) * (y_i[1] - y_i[0])),
            ima[cross_idx, cross_idx[::-1]], '--b', label=r'135$^\circ$-cut')

    axis.plot(x_i, airy[Npt // 2, ...], color='green', label='Bessel X-cut')
    axis.plot(y_i, airy[..., Npt // 2], color='cyan', label='Bessel Y-cut')

    axis.set_ylabel('PSF cross-sections')
    axis.set_xlabel(xlabel)
    axis.legend()
    axis.grid()

    xticks = np.array([-5.24, -4.24, -3.24, -2.23, -1.22, 0.0, 1.22, 2.23, 3.24, 4.24, 5.24]) / airy_scale
    axis.vlines(xticks, *axis.get_ylim(), colors='k', lw=2, alpha=0.5)
    axis.set_xticks(xticks)
    axis.get_xaxis().set_major_formatter(ticks.ScalarFormatter())
    axis.tick_params(labelrotation=45)

    axis.set_xlim(-plotscale, plotscale)

    axis.set_yscale(psf_scale)
    axis.set_ylim(1e-12, airy.max())

    axis.set_title(r"S{:02d} | F#{:.2f} | w{:.2f}{:s} | $\lambda${:3.2f}$\mu$m | P{:2.0f}%".format(
        key, item['fratio'], scale * item['wz'], unit, 1.0e6 * item['wl'], 100 * power))

    return
