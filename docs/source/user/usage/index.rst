.. _Use of PAOS:

=======================
Use of PAOS
=======================

`PAOS` was developed to study the effect of diffraction and aberrations impacting
the `Ariel` optical performance and related systematics.

The Ariel telescope is required to provide diffraction-limited capabilities
at wavelengths longer than :math:`3 \ \mu m`. While the Ariel measurements do not require
high imaging quality, they still need to have an efficient light bucket, i.e.
to collect photons in a sufficiently compact region of the focal plane.

PAOS was developed to demonstrate that even at wavelengths where Ariel is
not diffraction-limited it still delivers high quality data for scientific analysis.

`PAOS` can perform a large number of detailed analyses for any optical system
for which the Fresnel approximation holds (see :ref:`Fresnel diffraction theory`).

For `Ariel`, it can be used both on the instrument side and on the
optimization of the science return from the space mission. In this section,
a number of those uses are briefly described.


Aberrations
---------------------

`PAOS` can be used to quantitatively analyze the level of aberrations compatible
with the scientific requirements of the `Ariel` mission, for example to support the
maximum amplitude of the aberrations compatible with the scientific requirement for
the manufacturing of the `Ariel` telescope primary mirror (M1). `PAOS` can study the
effect of the aberrations to ensure that the optical quality, complexity, costs and
risks are not too high.

Gain noise
---------------------

`PAOS` can evaluate in a representative way the impact of optical diaphragms on the
photometric error in presence of pointing jitter and the impact of thermo-elastic variations
on optical efficiency during the flight. This impact has not been completely quantified,
especially at small wavelengths where the optical aberrations dominate and the Optical Transfer
Function (OTF) is very sensitive to their variation.

Pointing
---------------------

`PAOS` can be used to verify that the realistic PSFs of the mission are compatible with the
scientific requirements. For example, the FGS instrument (operating well under the diffraction limit)
uses the stellar photons to determine the pointing fluctuations by calculating the centroid of the
star position. This data is then used to stabilize the spacecraft through the Attitude Orbit
Control System (AOCS) of the spacecraft bus. If the PSF is too aberrated, the centroid might have
large errors, impacting the pointing stability and the measurement. Therefore, by delivering
realistic PSFs of the mission, `PAOS` can be used to estimate whether the pointing stability
is compatible with the scientific requirements, before having a system-level measurement that
will not be ready for several years.

Calibration
---------------------

`PAOS` can be used as a test bed to develop strategies for ground and in-flight calibration.
For instance, simulations of the re-focussing mechanism behind the M2 mirror (M2M), which uses
actuators on the M2 mirror to allow correction for misalignment generated during telescope
assembly or launch and cool-down to operating temperatures. These simulations could inform the
best strategy to optimize the telescope focussing ahead of payload delivery, ensuring that the
optical system stays focussed and satisfies the requirement on the maximum amplitude of the
wavefront aberrations during the measurements.




