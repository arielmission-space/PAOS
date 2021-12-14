Introduction
===============

What is PAOS?
-----------------
`PAOS`, the Physical Ariel Optics Simulator, is an End-to-End physical optics propagation model of the Ariel Telescope
and subsystems. `PAOS` was developed to demonstrate that even at wavelengths where it is not diffraction-limited Ariel
still delivers high quality data for scientific analysis. `PAOS` simulates the complex wavefront along the propagation axis,
and the Point Spread Function (PSF) at the focal planes. To do so, `PAOS` implements the Paraxial theory described
in `Lawrence et al., Applied Optics and Optical Engineering, Volume XI (1992) <https://ui.adsabs.harvard.edu/abs/1992aooe...11..125L>`_.
`PAOS` has been validated using the physical optics propagation library PROPER (see
`John E. Krist, SPIE (2007) <https://doi.org/10.1117/12.731179>`_).
In short, `PAOS` can study the effect of diffraction and aberrations impacting the optical performance and related systematics.
This allows performing a large number of detailed analyses, both on the instrument side and on the optimization of the
Ariel mission. Having a generic input system which mimics the Zemax OpticStudio :math:`^{©}` interface, `PAOS` allows the user
expert in CAD modeling to simulate other optical systems, as well.

.. note::
    `PAOS` v 0.0.2 works on Python 3+

    .. image:: _static/python-logo.png
        :width: 300
        :align: center

.. warning::
    `PAOS` is still under development. If you have any issue or find any bug, please report it to the developers.


Citing
--------
If you use this software or its products, please cite (Bocchieri A. - `PAOS` - *in prep*).


.. _changelog:

Changelog
---------
.. tip::
    Please note that `PAOS` does not implement an automatic updating system.
    Be always sure that you are using the most updated version by monitoring GitHub.

======= ========== ============================================================
Version Date       Changes
======= ========== ============================================================
0.0.2   15/09/2021 setting up new `PAOS` repository
0.0.2   20/10/2021 first documented `PAOS` release
======= ========== ============================================================
