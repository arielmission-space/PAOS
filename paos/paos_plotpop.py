import numpy as np
from matplotlib import pyplot as plt
from matplotlib.patches import Ellipse, Circle, Rectangle
from mpl_toolkits.axes_grid1 import make_axes_locatable


def simple_plot(fig, axis, key, item, ima_scale, surface_zoom=dict()):

    if item['wz'] < 0.005:
        # Use microns
        scale = 1.0e6
        unit = 'micron'
    else:
        # Use mm
        scale = 1.0e3
        unit = 'mm'

    ima = np.ma.masked_array(data=item['amplitude'] ** 2, mask=item['amplitude'] <= 0.0)
    power = ima.sum()
    if ima_scale == 'log':
        ima /= ima.max()
        im = axis.imshow(10 * np.ma.log10(ima), origin='lower', 
                        vmin=-20, vmax=0)
        cbar_label = 'power/pix [db]'
    elif ima_scale == 'linear':
        im = axis.imshow(ima, origin='lower')
        cbar_label = 'power/pix'
    else:
        raise KeyError('ima_scale shall be either log or linear')

    cax = make_axes_locatable(axis).append_axes('right', size='5%', pad=0.05)
    cbar = fig.colorbar(im, cax=cax, orientation='vertical')
    cbar.set_label(cbar_label)

    if item['aperture'] is not None:
        x, y = item['aperture'].positions
        dx, dy = item['dx'], item['dy']
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
            aper = Ellipse((0, 0), width=2 * arad, height=2 * arad, ec='k', lw=5, fill=False, alpha=0.5)
            axis.add_patch(aper)

    if beamradius < airyradius and (item['ABCDt']() != np.eye(2)).all() and np.isfinite(airyradius):
        plotscale = 5.24 * airyradius / 1.22  # 5th Airy null
    elif not item['aperture'] is None:
        plotscale = max(wx / 2, wy / 2)
    else:
        plotscale = beamradius

    if key in surface_zoom.keys():
        zoomout = surface_zoom[key]
    else:
        zoomout = 1
        
    axis.set_xlim(-zoomout * plotscale, zoomout * plotscale)
    axis.set_ylim(-zoomout * plotscale, zoomout * plotscale)
    axis.grid()

    axis.set_title("S{:02d} | F#{:.2f} | w{:.2f}{:s} | $\lambda${:3.2f}$\mu$m | P{:2.0f}%".format(
        key, item['fratio'],
        scale * item['wz'], unit, 1.0e6 * item['wl'], 100*power))
    axis.set_xlabel(unit)
    axis.set_ylabel(unit)

    return

def plot_pop(retval, ima_scale='log', ncols=2, figname=None, surface_zoom=dict()):

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
        else:
            i = k % ncols;
            j = k // ncols
            axis = ax[j, i]

        simple_plot(fig, axis, key, item, ima_scale, surface_zoom)

        if n_subplots % ncols and k == n_subplots - 1:
            for col in range(i+1, ncols):
                ax[j, col].set_visible(False)

    plt.show()
    
    if not figname is None:
        fig.savefig(figname, bbox_inches='tight', dpi=150)

    return
