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
    affiliation: "1,2,3"
  - name: Enzo Pascale
    orcid: 0000-0002-3242-8154
    affiliation: "1"            
affiliations:
 - name: Department of Physics, La Sapienza Università di Roma, Piazzale Aldo Moro 2, Roma, 00185, Italy
   index: 1
 - name: Department of Physics and Astronomy, University College London, Gower Street, London, WC1E 6BT, UK
   index: 2
 - name: INAF, Osservatorio Astronomico di Palermo, Piazza del Parlamento 1, Palermo, I-90134, Italy
   index: 3 
date: 27 January 2024
bibliography: paper.bib

---

# Summary

<!-- A summary describing the high-level functionality and purpose of the software for a diverse, non-specialist audience. -->

`PAOS` is an open-source code implementing physical optics propagation (POP) in Fresnel approximation and paraxial ray-tracing to analyze complex waveform propagation through both generic and off-axes optical systems, enabling the generation of realistic Point Spread Functions across various wavelengths and focal planes. It improves upon other POP codes offering extensive customization options and the liberty to access, utilize, and adapt the software library to the user's application. With a generic input system and a built-in Graphical User Interface, `PAOS` ensures seamless user interaction and facilitates simulations. The versatility of `PAOS` enables its application to a wide array of optical systems, extending beyond its initial use case. `PAOS` presents a fast, modern, and reliable POP simulation tool, enhancing the assessment of optical performance for a wide range of scientific and engineering applications and making advanced simulations more accessible and user-friendly.

Developed using a Python&thinsp;3 stack, `PAOS` is released under the BSD 3-Clause license and is available on [GitHub](https://github.com/arielmission-space/PAOS). The plugin can be installed from the source code or from [PyPI](https://pypi.org/project/paos/), so it can be installed as `pip install paos`. The documentation is available on [readthedocs](https://paos.readthedocs.io/en/latest/), including a quick-start guide, documented examples, a comprehensive description of the software functionalities, and guidelines for developers. The documentation is continuously updated and is versioned to match the software releases.

<!-- Mention PyPi and readthedocs -->

# Benchmark

<!-- A summary of the results of the benchmarking tests. -->

# Statement of need

<!-- A statement of need section that clearly illustrates the research purpose of the software and places it in the context of related work. -->

Accurate assessment of the optical performance of advanced telescopes and imaging systems is essential to achieve an optimal balance between optical quality, system complexity, costs, and risks. Optical system design has witnessed significant advancements in recent years, necessitating efficient and reliable tools to simulate and optimize complex systems [@Smith:2000]. Ray-tracing and Physical Optics Propagation (POP) are the two primary methods for modelling the propagation of electromagnetic fields through optical systems. Ray-tracing is often employed during the design phase due to its speed, flexibility, and efficiency in determining basic properties such as optical magnification, aberrations, and vignetting. POP provides a comprehensive understanding of beam propagation by directly calculating changes in the electromagnetic wavefront [@Goodman:2005]. POP is particularly useful for predicting diffraction effects and modelling the propagation of coherently interfering optical wavefronts. Yet, it may require supplementary input from direct measurements or a ray-tracing model for comprehensive analysis including aberration variations, especially in the Fresnel approximation. Commercial tools like `Zemax` and `Code V` enable POP calculations, offering advanced capabilities in aberration reduction and optical system optimization. However, these programs often come with substantial costs and steep learning curves, which may not be justifiable for every application. Furthermore, accessibility to their source code is often limited or not available.

To addresss these limitations, we developed `PAOS`, a reliable, user-friendly, and open-source POP code that integrates an implementation of Fourier optics. `PAOS` employs the Fresnel approximation for efficient and accurate optical system simulations. By including a flexible configuration file and paraxial ray-tracing, `PAOS` seamlessly facilitates the study of various optical systems, including non-axial symmetric ones, as long as the Fresnel approximation remains valid. Initially developed to evaluate the optical performance of the `Ariel` Space Mission [@Tinetti:2018;@Tinetti:2021], `PAOS` has proven its value in assessing the impact of diffraction, aberrations, and related systematics on `Ariel`'s optical performance. By offering a general-purpose tool capable of simulating the optical performance of diverse optical systems, `PAOS` fills a crucial gap in the field and makes advanced physical optics research more accessible.

# Acknowledgements

<!-- Acknowledgement of any financial support. -->

This work was supported by the Italian Space Agency (ASI) with `Ariel` grant n. 2021.5.HH.0.

# References

<!-- A list of key references, including to other software addressing related needs. Note that the references should include full names of venues, e.g., journals and conferences, not abbreviations only understood in the context of a specific discipline. -->