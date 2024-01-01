Introduction
===============

To model the propagation of an electromagnetic field through an optical system, one of two methods is usually adopted:

#. Ray-tracing, i.e. to estimate the path of individual, imaginary lines which represent normals to the wavefront (the
   surfaces of constant phase);
#. Physical optics propagation (POP), i.e. to estimate the changes in the wavefront as it travels through the optical
   components

These two methods yield different representations of the beam propagation and are used to different scopes.
Ray-tracing is typically used during the design phase as it is fast, flexible and extremely useful to determine the
basic properties of an optical system (magnification, aberrations, vignetting, etc.).

However, rays propagate along straight lines without interfering with one another and thus are not suitable to
predict the effects of diffraction. Conversely, POP models the propagation of wavefronts that coherently interfere
with themselves, but it cannot determine aberration changes (which must be input separately).

Propagation codes
---------------------

Several optical propagation codes exist, that implement ray-tracing or POP or combine the two. Widely used examples
include commercial ray-tracing programs like Code V :math:`^{©}` and Zemax OpticStudio :math:`^{©}` that also offer
POP calculations.

However, these programs are costly, require intense training and are not easily customizable to several needs
(e.g. Monte Carlo simulations to test wavefront aberration control). Free, publicly available propagation
codes, with access to source code are rare. Notable examples include:

* LightPipes

  a set of individual programs (originally in C, now in Python) that can be chained together to model the propagation
  through an optical system;
* POPPY

  a Python module originally developed as part of a simulation package for the James Webb Space Telescope, that
  implements an object-oriented system for modeling POP, particularly for telescopic and coronagraphic imaging;
* PROPER

  a library of optical propagation procedures and functions for the IDL (Interactive Data Language), Python,
  and Matlab environments, intended for exploring diffraction effects in optical systems.

However, these codes are not suitable to every application. For example, POPPY only supports image and pupil planes;
intermediate planes are stated as a future goal. PROPER, for its part "assumes an unfolded, linear layout and is not
suitable to propagate light through an optical system with optical surfaces that may be tilted or offset from the
optical axis". Moreover, none of these codes supports refractive elements.

About `PAOS`
------------
``PAOS``, the Physical `Ariel` Optics Simulator, is an End-to-End physical optics propagation model of the `Ariel` Telescope
and subsystems. ``PAOS`` was developed to demonstrate that even at wavelengths where it is not diffraction-limited
(:math:`\lambda < 3.0 \ \mu m`) `Ariel` still delivers high quality data for scientific analysis.

Having a generic input system which mimics the Zemax OpticStudio :math:`^{©}` interface, ``PAOS`` allows any user
expert in CAD modeling to simulate other optical systems, as well (see later in :ref:`Input system`).

``PAOS`` simulates the complex wavefront at each point along the propagation axis, and the Point Spread Function (PSF)
at the principal and intermediate focal planes. To do so, ``PAOS`` implements the Paraxial theory described
in `Lawrence et al., Applied Optics and Optical Engineering, Volume XI (1992) <https://ui.adsabs.harvard.edu/abs/1992aooe...11..125L>`_
(see later in :ref:`ABCD description`). ``PAOS`` implements a paraxial ray-tracing (see :ref:`Ray tracing`) to estimate
the projections of the physical apertures/obscurations, which is used to perform the propagation for an off-axis
optical system like the Ariel Telescope without incurring in phase aberrations that are large enough to cause
aliasing in the computational grid.

``PAOS`` automatizes the choice of algorithm to propagate the wavefront in near-field and far-field condition by using the
properties of the pilot beam, an analytically-traced on-axis Gaussian beam (see :ref:`Gaussian beams`).
``PAOS`` also supports the propagation through refractive media (see later in :ref:`Materials description`) and is
designed to facilitate Monte Carlo simulations for e.g. performance estimation for an ensemble of wavefront error
realizations, compatible with an optical performance requirement (see later in :ref:`Monte Carlo simulations`).

``PAOS`` has been validated using the physical optics propagation library PROPER
(`John E. Krist, PROPER: an optical propagation library for IDL, SPIE (2007) <https://doi.org/10.1117/12.731179>`_)
(see later in :ref:`Validation`).

In short, ``PAOS`` can study the effect of diffraction and aberrations impacting the optical performance and related systematics.
This allows performing a large number of detailed analyses, both on the instrument side and on the optimization of the
`Ariel` mission.
