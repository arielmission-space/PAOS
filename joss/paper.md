---
title: 'PAOS: a fast, modern, and reliable Python package for Physical Optics studies'
tags:
  - Physical Optics
  - Fresnel
  - Telescopes
  - Simulations
  - Python&thinsp;3
  - GUI
authors:
  - name: Andrea Bocchieri
    orcid: 0000-0002-8846-7961
    # equal-contrib: true
    affiliation: "1"
  - name: Lorenzo V. Mugnai
    orcid: 0000-0002-9007-9802
    affiliation: "2"
  - name: Enzo Pascale
    orcid: 0000-0002-3242-8154
    affiliation: "1"            
affiliations:
 - name: Department of Physics, La Sapienza Università di Roma, Piazzale Aldo Moro 5, Roma, 00185, Italy
   index: 1
 - name: School of Physics and Astronomy, Cardiff University, Queens Buildings, The Parade, Cardiff, CF24 3AA, UK
   index: 2
date: 19 April 2025
bibliography: paper.bib

---

# Summary

<!-- A summary describing the high-level functionality and purpose of the software for a diverse, non-specialist audience. -->

`PAOS` is an open-source code implementing physical optics propagation (POP) in Fresnel approximation and paraxial ray-tracing to analyze complex waveform propagation through both generic and off-axes optical systems. It enables the generation of realistic Point Spread Functions across various wavelengths and focal planes, and wavefront analyses at each point in the optical system. It improves upon other POP codes offering extensive customization options and the liberty to access, utilize, and adapt the software library to the user's application. With a generic input system and a built-in Graphical User Interface, `PAOS` ensures seamless user interaction and facilitates simulations. The versatility of `PAOS` enables its application to a wide array of optical systems, extending beyond its initial use case. `PAOS` presents a fast, modern, and reliable POP simulation tool, enhancing the assessment of optical performance for a wide range of scientific and engineering applications and making advanced simulations more accessible and user-friendly.

Developed using a Python&thinsp;3 stack, `PAOS` is released under the BSD 3-Clause license and is available on [GitHub](https://github.com/arielmission-space/PAOS). The package can be installed from the source code or from [PyPI](https://pypi.org/project/paos/), so it can be installed as `pip install paos`. The documentation is available on [readthedocs](https://paos.readthedocs.io/en/latest/), including a quick-start guide, documented examples, a comprehensive description of the software functionalities, and guidelines for developers. The documentation is continuously updated and is versioned to match the software releases.

<!-- Mention PyPi and readthedocs -->

# Benchmark

<!-- A summary of the results of the benchmarking tests. -->

We benchmarked `PAOS` against `PROPER` [@Krist:2007] on the HST optical system, because `PROPER` is not designed to handle a more complex optical system such as `Ariel`’s, which i) is off-axis and ii) involves other elements than simple thin lenses (e.g.&thinsp;dichroics). The description of the HST system used is the one provided in the `Hubble_simple.py` file in the `PROPER` package[^1]. This description was translated into an input file[^2] for `PAOS`. All simulation inputs have been matched (e.g., wavelength, grid size, `zoom`[^3]). We added a line in the `PROPER` HST routine to set the pixel subsampling factor used to antialias the edges of shapes. We set this value to 101 from the default 11 to more closely match the exact treatment given in `PAOS`.

We compared the resulting PSFs at the focal plane of the telescope, both in the central region and in the outer wings. The first benchmark is reported below, showing the results for the PSFs at 1 $\mu$m. \autoref{fig:benchmark-1} shows the central region of the HST PSFs as computed with `PAOS` and `PROPER`, and their difference. No significant residuals were found, with sporadic outlier pixels showing deviations by < 0.1 dB in regions corresponding to the PSF zeros due to small numerical errors.

![The central region of the HST PSF at 1 $\mu$m as estimated with PAOS (left) and `PROPER` (center) and normalized to the maximum value in the array. The axes are in oversampled pixels. The color scale represents the power per pixel in decibels (dB), with a lower cut-off at -60 dB for better visualization. The right panel reports the difference between the PSF computed with `PROPER` and `PAOS` in the same physical units. \label{fig:benchmark-1}](hubble_psf2d_comparison.pdf){height=100%}

\autoref{fig:benchmark-2} shows a detailed view of the slices of the PSFs along the horizontal and vertical axes, and their differences. The signal curves show an almost perfect overlap, with negligible residuals, all corresponding to values < -50 dB from the PSF maximum in the far wings.

![Comparison between PSF slices along the x and y axis, respectively. The left column reports the slice values for both codes, whilst the right column reports their difference. The units are the same (power per pixel in dB) to highlight even the smallest discrepancies. As can be observed, these differences are negligible for powers $\gtrsim$-50 dB for the HST application. \label{fig:benchmark-2}](hubble_psf_comparison.pdf){height=100%}

\autoref{fig:benchmark-aberrated-1} and \ref{fig:benchmark-aberrated-2} report the second benchmark; in this case, we simulate an aberrated HST PSF, where the wavefront error (WFE) is described by a superposition of Zernike polynomials. At M2, we added 100 nm RMS (WFE) each for defocus, vertical astigmatism, and oblique astigmatism, totaling $\sigma \approx$ 173.2 nm WFE. The simulation is performed at $\lambda$ = 1.0 $\mu$m; therefore, using the Ruze formula [@Ross:2009], the Strehl ratio is $S = \exp\left(- 2 \pi \sigma / \lambda \right)\approx$ 0.3. Consequently, the PSF is highly aberrated and the main lobe is spread over more pixels. Thus, we can validate the `PAOS` implementation of optical aberrations, and we have a larger region of high signal. The latter is especially useful for investigating aliasing errors, which tend to occur more severely where the distribution has the highest amplitude because the amplitudes of the signal and the error add rather than the intensities [@Lawrence:1992].

![Same as \autoref{fig:benchmark-1}, but adding an optical aberration using Zernike polynomials: 100 nm RMS (WFE) for each of three low-order coefficients in the Zernike expansion: defocus and primary astigmatism (vertical and oblique), corresponding to the coefficients 4, 5, and 6 in the Noll ordering, respectively. The difference between the large-scale features of the PSFs is negligible. \label{fig:benchmark-aberrated-1}](hubble_psf2d_comparison_aberrated.pdf){height=100%}

![Comparison between the slices of the aberrated PSFs along the x and y axis, respectively. Locally, slightly `hotter` and `colder` pixels can be identified in the PSF wings, although, for powers $\gtrsim$-50 dB, this happens only sporadically. These minute numerical differences may be caused by the different treatment of aperture edges (exact for `PAOS`, sub-pixelled for `PROPER`), causing tiny aliasing errors. \label{fig:benchmark-aberrated-2}](hubble_psf_comparison_aberrated.pdf){height=100%}

We find that the differences between the aberrated PSFs are negligible and reach peaks of a few dB only in the far wings. However, even in the central region, there is an increase in `hot` and `cold` pixels compared to the unaberrated case. These discrepancies are probably due to the different treatment of the edges of apertures and vanes in the optical system, causing small aliasing errors when not exact. However, they are so tiny that they can be safely neglected for the HST application.

In summary, we find that `PAOS` is a robust and reliable tool for simulating the propagation of optical wavefronts through complex optical systems, as shown by the excellent agreement with the results obtained with `PROPER` for HST in our benchmark tests.

[^1]: The `PROPER` source code and documentation can be downloaded at <https://proper-library.sourceforge.net/>.
[^2]: `Hubble_simple.ini`, included in the package under the `lens data` directory for reproducibility.
[^3]: The ratio between the grid's linear dimension and the beam size at the initial surface.

# Statement of need

<!-- A statement of need section that clearly illustrates the research purpose of the software and places it in the context of related work. -->

Accurate assessment of the optical performance of advanced telescopes and imaging systems is essential to achieve an optimal balance between optical quality, system complexity, costs, and risks. Optical system design has witnessed significant advancements in recent years, necessitating efficient and reliable tools to simulate and optimize complex systems [@Smith:2000]. Ray-tracing and Physical Optics Propagation (POP) are the two primary methods for modelling the propagation of electromagnetic fields through optical systems. Ray-tracing is often employed during the design phase due to its speed, flexibility, and efficiency in determining basic properties such as optical magnification, aberrations, and vignetting. POP provides a comprehensive understanding of beam propagation by directly calculating changes in the electromagnetic wavefront [@Goodman:2005]. POP is particularly useful for predicting diffraction effects and modelling the propagation of coherently interfering optical wavefronts. Yet, it may require supplementary input from direct measurements or a ray-tracing model for comprehensive analysis including aberration variations, especially in the Fresnel approximation. Commercial tools like `Zemax` and `Code V` enable POP calculations, offering advanced capabilities in aberration reduction and optical system optimization. However, these programs often come with substantial costs and steep learning curves, which may not be justifiable for every application. Furthermore, accessibility to their source code is often limited or not available.

To addresss these limitations, we developed `PAOS`, a reliable, user-friendly, and open-source POP code that integrates an implementation of Fourier optics. `PAOS` employs the Fresnel approximation for efficient and accurate optical system simulations. By including a flexible configuration file and paraxial ray-tracing, `PAOS` seamlessly facilitates the study of various optical systems, including non-axial symmetric ones, as long as the Fresnel approximation remains valid. Initially developed to evaluate the optical performance of the `Ariel` Space Mission [@Tinetti:2018;@Tinetti:2021], `PAOS` has proven its value in assessing the impact of diffraction, aberrations, and related systematics on `Ariel`'s optical performance. By offering a general-purpose tool capable of simulating the optical performance of diverse optical systems, `PAOS` fills a crucial gap in the field and makes advanced physical optics research more accessible.

# Acknowledgements

<!-- Acknowledgement of any financial support. -->

This work was supported by the Italian Space Agency (ASI) with `Ariel` grant n. 2021.5.HH.0.

# References

<!-- A list of key references, including to other software addressing related needs. Note that the references should include full names of venues, e.g., journals and conferences, not abbreviations only understood in the context of a specific discipline. -->