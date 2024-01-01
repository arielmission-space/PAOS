.. _Compatibility of PAOS:

=======================
Compatibility of `PAOS`
=======================

``PAOS`` is compatible with existing `Ariel` simulators, such as

#. :ref:`ArielRad`
#. :ref:`Exosim`

.. _compat:

.. figure:: compat.png
   :align: center

   `PAOS compatibility with existing Ariel simulators`

.. _ArielRad:

ArielRad
-----------

`ArielRad` is the `Ariel` radiometric model simulator, that by implementing a detailed payload model is
capable of producing radiometric estimates of the uncertainties of the detection. `ArielRad` is used to
assess the payload science performance and demonstrate its compliance with the science requirements, by
creating and maintaining the top level payload performance error budgets, allowing a balanced allocation
of resources across the payload. For more details, please refer to the
`ArielRad documentation <https://github.com/arielmission-space/ArielRad2>`_ and the paper
`L. V. Mugnai, et al. ArielRad: the Ariel radiometric model. Exp Astron 50, 303–328 (2020) <https://doi.org/10.1007/s10686-020-09676-7>`_;.

``PAOS`` can produce representative aberrated PSFs for every `Ariel` wavelength and focal plane from which the
optical efficiency :math:`\eta_{opt}` can be estimated, i.e. the fraction of photons that enter the telescope and
are transferred to the detector focal planes. `ArielRad` can use this estimates to update its current
signal estimates and noise budget, ensuring that the `Ariel` mission always has updated and realistic information
on payload performance and compliance with science requirements.

.. _ExoSim:

ExoSim
-----------

`ExoSim` is an end-to-end, time-domain simulator of `Ariel` observations. It evaluates photometric and
spectroscopic light curves implementing a detailed description of the instrument design, source of
uncertainties, and systematics of instrument and astrophysical origin. `ExoSim` simulations
allow us to study effects of spatially and temporally correlated noise processes such as the
photometric uncertainties arising from the jitter of the line of sight, or from the activity of
the host star.

`ExoSim2.0`, a refactored version of `ExoSim`, is currently being developed, with in-place infrastructure to
load and use PSFs created with ``PAOS``. This allows `ExoSim2.0` to produce realistic images on the focal planes
of the instruments using representative aberrated PSFs. For more details, please refer to the `ExoSim2.0
documentation <https://github.com/arielmission-space/ExoSim2.0>`_ and the paper
`Sarkar, S., Pascale, E., Papageorgiou, A. et al. ExoSim: the Exoplanet Observation Simulator. Exp Astron 51, 287–317 (2021)
<https://doi.org/10.1007/s10686-020-09690-9>`_
