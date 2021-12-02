.. _ABCD description:

=======================
ABCD description
=======================

`PAOS` implements the paraxial theory described in
`Lawrence et al., Applied Optics and Optical Engineering, Volume XI (1992) <https://ui.adsabs.harvard.edu/abs/1992aooe...11..125L>`_

The paraxial region
-----------------------

For self-consistency, we give a definition for paraxial region, following
`Smith, Modern Optical Engineering, Third Edition (2000) <https://spie.org/Publications/Book/387098>`_.

The paraxial region of an optical system is a thin threadlike region about the optical axis
where all the slope angles and the angles of incidence and refraction may be set equal to their
sines and tangents.

Optical coordinates
-----------------------

The `PAOS` code implementation assumes optical coordinates as defined in the diagram below.

.. image:: coordinates.png
   :width: 600
   :align: center

where

#. :math:`z_{1}` is the coordinate of the object (:math:`<0` in the diagram)
#. :math:`z_{2}` is the coordinate of the image (:math:`>0` in the diagram)
#. :math:`u_{1}` is the slope, i.e. the tangent of the angle = angle in paraxial approximation; :math:`u_{1} > 0` in the diagram.
#. :math:`u_{2}` is the slope, i.e. the tangent of the angle = angle in paraxial approximation; :math:`u_{2} < 0` in the diagram.
#. y is the coordinate where the rays intersect the thin lens (coloured in red in the diagram).

The (thin) lens equation is

.. math::
    -\frac{1}{z_1}+\frac{1}{z_2} = \frac{1}{f}
    :label:

where :math:`f` is the lens focal length: :math:`f > 0` causes the beam to be more convergent,
while :math:`f < 0` causes the beam to be more divergent.

The tangential plane is the YZ plane and the sagittal plane is the XZ plane.

ABCD ray tracing
----------------------------

Paraxial ray tracing in the tangential plane (YZ) can be done by defining the vector :math:`\vec{v_{t}}=(y, u_{y})`
which describes a ray propagating in the tangential plane.
Paraxial ray tracing can be done using ABCD matrices (see later in :ref:`Optical system equivalent`).

.. note::
    In the sagittal plane, the same equation apply, modified when necessary when cylindrical symmetry is violated.
    The relevant vector is :math:`\vec{v_{s}}=(x, u_{x})`.

Propagation
----------------------------

Either in free space or in a refractive medium, propagation over a distance :math:`t` (positive left
:math:`\rightarrow` right) is given by

.. math::
    \begin{pmatrix}
    y_2\\
    u_2
    \end{pmatrix} =
    \begin{pmatrix}
    1 & t\\
    0 & 1
    \end{pmatrix}
    \begin{pmatrix}
    y_1\\
    u_1
    \end{pmatrix} =
    \hat{T}
    \begin{pmatrix}
    y_1 \\
    u_1
    \end{pmatrix}
    :label:

Thin lenses
----------------------------

A thin lens changes the slope angle and this is given by

.. math::
    \begin{pmatrix}
    y_2\\
    u_2
    \end{pmatrix} =
    \begin{pmatrix}
    1 & 0\\
    -\Phi & 1
    \end{pmatrix}
    \begin{pmatrix}
    y_1\\
    u_1
    \end{pmatrix} =
    \hat{L}
    \begin{pmatrix}
    y_1 \\
    u_1
    \end{pmatrix}
    :label:

where :math:`\Phi = \frac{1}{f}` is the lens optical power.

Dioptre
----------------------------

When light propagating from a medium with refractive index n1 enters in a dioptre of refractive index n2,
the slope varies as

.. math::
    \begin{pmatrix}
    y_2\\
    u_2
    \end{pmatrix} =
    \begin{pmatrix}
    1 & 0\\
    -\frac{\Phi}{n_2} & \frac{n_1}{n_2}
    \end{pmatrix}
    \begin{pmatrix}
    y_1\\
    u_1
    \end{pmatrix} =
    \hat{D}
    \begin{pmatrix}
    y_1 \\
    u_1
    \end{pmatrix}
    :label:

with the dioptre power :math:`\Phi = \frac{n_2-n_1}{R}`, where R is the radius of curvature.

.. note::
    :math:`R>0` if the centre of curvature is at the right of the dioptre and :math:`R<0` if at the left.

Medium change
----------------------------

The limiting case of a dioptre with :math:`R \rightarrow \infty` represents a change of medium.

.. math::
    \begin{pmatrix}
    y_2\\
    u_2
    \end{pmatrix} =
    \begin{pmatrix}
    1 & 0\\
    0 & \frac{n_1}{n_2}
    \end{pmatrix}
    \begin{pmatrix}
    y_1\\
    u_1
    \end{pmatrix} =
    \hat{N}
    \begin{pmatrix}
    y_1 \\
    u_1
    \end{pmatrix}
    :label:

Thick lenses
----------------------------

A real (thick) lens is modelled as

.. math::
    \begin{pmatrix}
    y_2\\
    u_2
    \end{pmatrix} =
    \hat{D_b}\hat{T}\hat{D_a}
    \begin{pmatrix}
    y_1 \\
    u_1
    \end{pmatrix}
    :label:

i.e. propagation through the dioptre :math:`D_a` (first encountered by the ray), then a propagation in the medium,
followed by the exit dioptre :math:`D_b`.

.. note::
    When the thickness of the dioptre, :math:`t`, is negligible and can be set to zero, this gives back the
    thin lens ABCD matrix.

.. _Magnification:

Magnification
----------------------------

A magnification is modelled as

.. math::
    \begin{pmatrix}
    y_2\\
    u_2
    \end{pmatrix} =
    \begin{pmatrix}
    M & 0\\
    0 & 1/M
    \end{pmatrix} =
    \hat{M}
    \begin{pmatrix}
    y_1 \\
    u_1
    \end{pmatrix}
    :label:

Prism
----------------------------

The prism changes both the slope and the magnification. Following
`J. Taché, "Ray matrices for tilted interfaces in laser resonators," Appl. Opt. 26, 427-429 (1987) <https://www.osapublishing.org/viewmedia.cfm?r=1&rwjcode=ao&uri=ao-26-3-427&html=true>`_
we report the ABCD matrices for the tangential and sagittal transfer:

.. math::
    P_{t} =
    \begin{pmatrix}
    \frac{cos(\theta_{4})}{cos(\theta_{3})} & 0\\
    0 & \frac{n cos(\theta_{3})}{cos(\theta_{4})}
    \end{pmatrix}
    \begin{pmatrix}
    1 & L\\
    0 & 1
    \end{pmatrix}
    \begin{pmatrix}
    \frac{cos(\theta_{2})}{cos(\theta_{1})} & 0\\
    0 & \frac{cos(\theta_{1})}{n cos(\theta_{2})}
    \end{pmatrix}
    :label:

.. math::
    P_{s} =
    \begin{pmatrix}
    1 & \frac{L}{n}\\
    0 & 1
    \end{pmatrix}
    :label:

where n is the refractive index of the prism, L is the geometrical path length of the prism, and the
angles :math:`\theta_i` are as described in Fig.2 from the paper, reported in the image below.

.. image:: prism.png
   :width: 600
   :align: center

.. _Optical system equivalent:

Optical system equivalent
----------------------------

The ABCD matrix method is a convenient way of treating an arbitrary optical system in the paraxial approximation.
This method is used to describe the paraxial behavior, as well as the Gaussian beam properties and the general
diffraction behaviour.

Any optical system can be considered a black box described by an effective ABCD matrix.
This black box and its matrix can be decomposed into four, non-commuting elementary operations (primitives):

#. magnification change
#. change of refractive index
#. thin lens
#. translation of distance (thickness)

Explicitly:

.. math::
    \begin{pmatrix}
    A & B\\
    C & D
    \end{pmatrix} =
    \begin{pmatrix}
    1 & t\\
    0 & 1
    \end{pmatrix}
    \begin{pmatrix}
    1 & 0\\
    -\Phi & 1
    \end{pmatrix}
    \begin{pmatrix}
    1 & 0\\
    0 & n_1/n_2
    \end{pmatrix}
    \begin{pmatrix}
    M & 0\\
    0 & 1/M
    \end{pmatrix} =
    \hat{T}\hat{L}\hat{N}\hat{M}
    :label:

where the four free parameters :math:`t`, :math:`\Phi`, :math:`n_1/n_2`, :math:`M` are, respectively, the effective
thickness, power, refractive index ratio, and magnification. Not to be confused with thickness, power, refractive
index ratio, and magnification of the optical system under study and its components.

All diffraction propagation effects occur in the single propagation step of distance :math:`t`.
Only this step requires any substantial computation time.

The parameters are estimated as follows:

.. math::
      M = \frac{A D - B C}{D} \\
      n_1/n_2 = M D \\
      t = \frac{B}{D} \\
      \Phi = - \frac{C}{M}
    :label:

With these definitions, the effective focal length is

.. math::
    f_{eff} = \frac{1}{\Phi M}
    :label:
