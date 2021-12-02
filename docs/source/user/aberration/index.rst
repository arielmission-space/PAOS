.. _Aberration description:

=======================
Aberration description
=======================

Zernike polynomials
-----------------------

`PAOS` models an aberration using a series of Zernike polynomials, up to a specified radial order.

`PAOS` can generate both ortho-normal polynomials and orthogonal polynomials as described in
`Laksminarayan & Fleck, Journal of Modern Optics (2011) <https://doi.org/10.1080/09500340.2011.633763>`_

The ordering can be either ANSI (default), or Noll, or Fringe, or Standard (Born&Wolf).

Example of an aberrated pupil
------------------------------

An example of aberrated PSFs at the `Ariel` Telescope exit pupil is shown below.

.. image:: aberrations.png
   :width: 600
   :align: center

In this figure, the same Surface Form Error (SFE) of :math:`50 \ nm` root mean square (r.m.s.)
is allocated to different aberrations, modeled as Zernike Polynomials. Starting from the top left
panel (oblique Astigmatism), seven such simulations are shown, in ascending Ansi order. Each
aberration differs in the impact on the Telescope optical quality: some (e.g. Coma) require a
more stringent allocation to be compatible with the mission scientific requirements.


Strehl ratio
-----------------

Encircled energy
------------------

