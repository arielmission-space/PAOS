.. _Materials description:

Materials description
=======================

Brief description of dispersion of light by optical materials and how it is implemented in `PAOS`.

In `PAOS`, this is handled by the class :class:`~paos.util.material.Material`.

Light dispersion
------------------

In optics, dispersion is the phenomenon in which the phase velocity of a wave depends on its frequency:

.. math::
    v={\frac {c}{n}}

where :math:`c` is the speed of light in a vacuum and :math:`n` is the refractive index of the dispersive medium.
Physically, dispersion translates in a loss of kinetic energy through absorption. The absorption by the dispersive medium
is different at different wavelengths, changing the angle of refraction of different colors of light as seen in the spectrum
produced by a dispersive prism and in chromatic aberration of (thick) lenses.

This can be seen in geometric optics from Snell's law:

.. math::
    \frac{sin(\theta_2)}{sin(\theta_1)} = \frac{n_1}{n_2}

that describes the relationship between the angle of incidence :math:`\theta_1` and refraction :math:`\theta_2` of light
passing through a boundary between an isotropic medium with refractive index :math:`n_1` and another with :math:`n_2`.

For air and optical glasses, for visible and infra-red light refraction indices :math:`n` decrease with increasing
:math:`\lambda` (`normal dispersion`), i.e.

.. math::
    \frac{d n}{d \lambda} < 0

while for ultraviolet the opposite behaviour is typically the case (anomalous dispersion).

See later in :ref:`Plotting refractive indices` for the behaviour of supported optical materials in `PAOS`.

Supported materials
-------------------------

Example
~~~~~~~~~~~

.. code-block:: python

        from paos.util.material import Material

        wl = 1.95  # micron
        mat = Material(wl)
        print('Supported materials: ')
        print(*mat.materials.keys(), sep = "\n")

Sellmeier equation
---------------------

The Sellmeier equation is an empirical relationship for the dispersion of light in a particular transparent
medium such as an optical glass in function of wavelength. In its original form (Sellmeier, 1872) it is given as

.. math::
    n^{2}(\lambda )=1+\sum _{i}{\frac {K_{i}\lambda ^{2}}{\lambda ^{2}-L_{i}}}
    :label:

where :math:`n` is the refractive index, :math:`\lambda` is the wavelength and :math:`K_i` and :math:`\sqrt{L_i}`
are the Sellmeier coefficients, determined from experiments.

Physically, each term of the sum represents an absorption resonance of strength :math:`K_i` at wavelength
:math:`\sqrt{L_i}`. Close to each absorption peak, a more precise model of dispersion is required to avoid non-physical
values.

`PAOS` implements the Sellmeier 1 equation (Zemax OpticStudio :math:`^{©}` notation) to estimate the index of refraction
relative to air for a particular optical galss at the glass reference temperature and pressure

.. math::
    T_{ref} = 20^{\circ} \\
    P_{ref} = 1 \ atm
    :label:

This form of the original equation consists of only three terms and is given as

.. math::
    n^{2}(\lambda )=1+{\frac {K_{1}\lambda ^{2}}{\lambda ^{2}-L_{1}}}+{\frac {K_{2}\lambda ^{2}}{\lambda ^{2}-L_{2}}}+{\frac {K_{3}\lambda ^{2}}{\lambda ^{2}-L_{3}}}
    :label:

The resulting refracting index should deviate from the actual refractive index by a quantity which is of the
order of the homogeneity of a glass sample (see e.g. `Optical properties <http://oharacorp.com/o2.html>`_).

Example
~~~~~~~~~

Code snippet to use :class:`~paos.util.material.Material` to estimate the index of refraction of borosilicate crown
glass (known as `BK7`) for a range of wavelengths from the visible to the infra-red.

.. code-block:: python

        import numpy as np
        from paos.util.material import Material

        glass = 'bk7'

        mat = Material(wl=np.linspace(0.5, 8.0, 10))
        print('Sellmeier refractive index: ')
        material = mat.materials[glass.upper()]
        mat.sellmeier(material['sellmeier'])


Temperature and refractive index
-----------------------------------

Refractive index is affected by changes in the temperature of the dispersive medium.

Air

Estimate the air index of refraction at wavelength :math:`\lambda`, temperature :math:`T`,
and relative pressure :math:`P`.

.. math::
    n_{ref} = 1.0 + 1.0 \cdot 10^{-8} \left(6432.8 + \frac{2949810 \lambda^2}{146 \lambda^2 - 1} + 25540 \frac{\lambda^2}{41 \lambda^2 - 1}\right)
    :label:

.. math::
    n_{air} = 1 + \frac{P \left(n_{ref} - 1\right)} {1.0 + 3.4785 \cdot 10^{-3} (T - 15)}
    :label:


This can be ascertained through the temperature
coefficient of refractive index. The temperature coefficient of refractive index is defined as dn/dt from the
curve showing the relationship between glass temperature and refractive index. The temperature coefficient of
refractive index (for light of a given wavelength) changes with wavelength and temperature.

Therefore, the Abbe number also changes with temperature. There are two ways of showing the temperature
coefficient of refractive index. One is the absolute coefficient (dn/dt absolute ) measured under vacuum and the
other is the relative coefficient (dn/dt relative ) measured at ambient air (101.3 kPa {760 torr} dry air).


.. math::
    n(\Delta T) = \frac{n^2 - 1}{2 n} D_0 \Delta T + n
    :label:


Example
~~~~~~~~~~

.. code-block:: python

        from paos.util.material import Material

        wl = 1.95  # micron
        mat = Material(wl)
        glass = 'bk7'
        print('absolute index of refraction {:.4f} \nindex relative to air {:.4f}'.format(
            *mat.nmat(glass)), sep = "\n")


.. _Plotting refractive indices:

Plotting refractive indices
----------------------------

:numref:`matplot`

.. _matplot:

.. figure:: mat.png
   :width: 1200
   :align: center

   `Relative index of supported materials`

Example
~~~~~~~~~