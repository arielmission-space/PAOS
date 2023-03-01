.. _Plotting results:

Plotting results
=======================

`PAOS` implements different plotting routines, summarized here, that can be used to give a complementary idea of
the main POP simulation results.

Base plot
-------------

The base plot method, :func:`~paos.core.plot.simple_plot`, receives as input the POP output dictionary and the
dictionary key of one optical surface and plots the squared amplitude of the wavefront at the given optical surface.

Example
~~~~~~~~~

Code example to use :func:`~paos.core.plot.simple_plot` to plot the expected PSF at the image plane of the
EXCITE optical chain.

.. jupyter-execute::
        :hide-code:
        :stderr:
        :hide-output:

        from paos.core.parseConfig import parse_config
        from paos.core.run import run
        pup_diameter, parameters, wavelengths, fields, opt_chains = parse_config('../lens data/Excite_TEL.ini')
        ret_val = run(pup_diameter, 1.0e-6 * wavelengths[0], parameters['grid_size'], parameters['zoom'], fields[0], opt_chains[0])

.. jupyter-execute::

        import matplotlib.pyplot as plt
        from paos.core.plot import simple_plot

        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(1,1,1)

        key = list(ret_val.keys())[-1]  # plot at last optical surface
        simple_plot(fig, ax, key=key, item=ret_val[key], ima_scale='log')

        plt.show()

The cross-sections for this PSF can be plotted using the method :func:`~paos.core.plot.plot_psf_xsec`, as shown below.

.. jupyter-execute::

        from paos.core.plot import plot_psf_xsec

        fig = plt.figure(figsize=(9, 8))
        ax = fig.add_subplot(1,1,1)

        key = list(ret_val.keys())[-1]  # plot at last optical surface
        plot_psf_xsec(fig, ax, key=key, item=ret_val[key], ima_scale='log')

        plt.show()


POP plot
------------

The POP plot method, :func:`~paos.core.plot.plot_pop`, receives as input the POP output dictionary plots the squared
amplitude of the wavefront at all available optical surfaces.

Example
~~~~~~~~~

Code example to use :func:`~paos.core.plot.plot_pop` to plot the squared amplitude of the wavefront at all surfaces
of the EXCITE optical chain.

.. jupyter-execute::

        from paos.core.plot import plot_pop
        plot_pop(ret_val, ima_scale='log', ncols=2)
