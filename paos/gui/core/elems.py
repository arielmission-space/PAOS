from shiny import ui

from paos import PSD, Zernike
from paos.gui.core.shared import (
    CARD_HEADER_CLASS,
    ICONS,
    nested_div,
    output_text_verbatim,
    vspace,
)

Placeholder = {
    "Par1": {
        "INIT": "",
        "Coordinate Break": "Xdecenter",
        "Standard": "",
        "Paraxial Lens": "Focal length",
        "ABCD": "Ax",
        "Zernike": "Wavelength",
        "PSD": "A",
        "Grid Sag": "Wavelength",
    },
    "Par2": {
        "INIT": "",
        "Coordinate Break": "Ydecenter",
        "Standard": "",
        "Paraxial Lens": "",
        "ABCD": "Bx",
        "Zernike": "Ordering",
        "PSD": "B",
        "Grid Sag": "Nx",
    },
    "Par3": {
        "INIT": "",
        "Coordinate Break": "Xtilt",
        "Standard": "",
        "Paraxial Lens": "",
        "ABCD": "Cx",
        "Zernike": "Normalization",
        "PSD": "C",
        "Grid Sag": "Ny",
    },
    "Par4": {
        "INIT": "",
        "Coordinate Break": "Ytilt",
        "Standard": "",
        "Paraxial Lens": "",
        "ABCD": "Dx",
        "Zernike": "Radius of S.A.",
        "PSD": "fknee",
        "Grid Sag": "Dx",
    },
    "Par5": {
        "INIT": "",
        "Coordinate Break": "",
        "Standard": "",
        "Paraxial Lens": "",
        "ABCD": "Ay",
        "Zernike": "Origin",
        "PSD": "fmin",
        "Grid Sag": "Dy",
    },
    "Par6": {
        "INIT": "",
        "Coordinate Break": "",
        "Standard": "",
        "Paraxial Lens": "",
        "ABCD": "By",
        "Zernike": "Orthonorm",
        "PSD": "fmax",
        "Grid Sag": "Xdecenter (pix)",
    },
    "Par7": {
        "INIT": "",
        "Coordinate Break": "",
        "Standard": "",
        "Paraxial Lens": "",
        "ABCD": "Cy",
        "Zernike": "",
        "PSD": "SR",
        "Grid Sag": "Ydecenter (pix)",
    },
    "Par8": {
        "INIT": "",
        "Coordinate Break": "",
        "Standard": "",
        "Paraxial Lens": "",
        "ABCD": "Dy",
        "Zernike": "",
        "PSD": "units",
        "Grid Sag": "Errormap filepath",
    },
}


def app_elems(config):
    general_elems = [
        ui.input_text(
            "project",
            "Project name",
            value=config["general"].get("project", "Template"),
        ),
        ui.input_text("comment", "Comment", value=config["general"].get("comment", "")),
        ui.input_text(
            "version",
            "Version",
            value=config["general"].get("version", "0.1"),
        ),
        ui.input_text(
            "grid_size",
            "Grid size",
            value=config["general"].getint("grid_size", "512"),
        ),
        ui.input_text("zoom", "Zoom", value=config["general"].getint("zoom", "4")),
        ui.input_text(
            "tambient",
            "Ambient temperature [°C]",
            value=config["general"].getfloat("tambient", "20.0"),
        ),
        ui.input_text(
            "pambient",
            "Ambient pressure [atm]",
            value=config["general"].getfloat("pambient", "1.0"),
        ),
        ui.tags.div(
            ui.tags.label("Wavelength unit", class_="form-label"),
            ui.tags.input(
                id="wavelength_unit",
                type="text",
                value=config["general"].get("wavelength_unit", "micron"),
                readonly=True,
                class_="form-control",
            ),
        ),
        vspace,
        ui.tags.div(
            ui.tags.label("Angle unit", class_="form-label"),
            ui.tags.input(
                id="angle_unit",
                type="text",
                value=config["general"].get("angle_unit", "deg"),
                readonly=True,
                class_="form-control",
            ),
        ),
        vspace,
        ui.tags.div(
            ui.tags.label("Lens unit", class_="form-label"),
            ui.tags.input(
                id="lens_unit",
                type="text",
                value=config["general"].get("lens_unit", "m"),
                readonly=True,
                class_="form-control",
            ),
        ),
    ]

    field_elems = {}
    for n, (key, value) in enumerate(config.items("fields")):
        n += 1
        field_elems[n] = {}
        field_elems[n]["#"] = {
            "f": ui.p,
            "width": 5,
            "value": n,
        }
        field_elems[n]["Field"] = {
            "f": ui.input_text,
            "id": key,
            "value": value,
            "width": 7,
        }

    wl_elems = {}
    for n, (key, value) in enumerate(config.items("wavelengths")):
        n += 1
        wl_elems[n] = {}
        wl_elems[n]["#"] = {
            "f": ui.p,
            "width": 5,
            "value": n,
        }
        wl_elems[n]["Wavelength"] = {
            "f": ui.input_text,
            "id": key,
            "value": value,
            "width": 7,
        }

    lens_elems = {}
    for key in config.sections():
        if not key.startswith("lens_"):
            continue
        n = int(key.split("_")[1])
        item = config[key]

        lens_elems[n] = {}
        lens_elems[n]["#"] = {
            "f": ui.p,
            "width": 1,
            "value": n,
        }
        surface_type = item.get("surfacetype")
        lens_elems[n]["SurfaceType"] = {
            "f": ui.tags.input,
            # "choices": [
            #     "INIT",
            #     "Coordinate Break",
            #     "Standard",
            #     "Paraxial Lens",
            #     "ABCD",
            #     "Zernike",
            #     "PSD",
            #     "Grid Sag",
            # ],
            "width": 1,
            "value": surface_type,
            # "selected": surface_type,
            "prefix": "lens_",
            "readonly": True,
        }
        lens_elems[n]["Comment"] = {
            "f": ui.input_text,
            "value": item.get("comment"),
            "width": 1,
            "prefix": "lens_",
        }
        lens_elems[n]["Radius"] = {
            "f": ui.input_text,
            "value": item.get("radius", ""),
            "width": 1,
            "prefix": "lens_",
        }
        lens_elems[n]["Thickness"] = {
            "f": ui.input_text,
            "value": item.get("thickness", ""),
            "width": 1,
            "prefix": "lens_",
        }
        lens_elems[n]["Material"] = {
            "f": ui.input_select,
            "choices": [
                "",
                "MIRROR",
                "BK7",
                "BAF2",
                "CAF2",
                "SAPPHIRE",
                "SF11",
                "ZNSE",
            ],
            "width": 1,
            "selected": item.get("material", ""),
            "prefix": "lens_",
        }
        lens_elems[n]["Save"] = {
            "f": ui.input_checkbox,
            "value": item.getboolean("save", True),
            "width": 1,
            "prefix": "lens_",
        }
        lens_elems[n]["Ignore"] = {
            "f": ui.input_checkbox,
            "value": item.getboolean("ignore", False),
            "width": 1,
            "prefix": "lens_",
        }
        lens_elems[n]["Stop"] = {
            "f": ui.input_checkbox,
            "value": item.getboolean("stop", False),
            "width": 1,
            "prefix": "lens_",
        }
        aperture = item.get("aperture", "")
        if aperture != "":
            aperture = " ".join(aperture.split())
            aperture = aperture.split(",")
            aperture_type = str(aperture[0])
            xhw = float(aperture[1])
            yhw = float(aperture[2])
            xdecenter = float(aperture[3])
            ydecenter = float(aperture[4])
        else:
            aperture_type = xhw = yhw = xdecenter = ydecenter = ""
        lens_elems[n]["Aperture"] = {
            "title": "Settings",
            "f": ui.popover,
            "width": 1,
            "value": {
                "Aperture_Type": {
                    "f": ui.input_select,
                    "selected": aperture_type,
                    "choices": [
                        "",
                        "rectangular aperture",
                        "rectangular obscuration",
                        "elliptical aperture",
                        "elliptical obscuration",
                    ],
                    "label": "Type",
                    "prefix": "lens_",
                },
                "Aperture_xhw": {
                    "f": ui.input_text,
                    "value": xhw,
                    "label": "X-Half Width",
                    "prefix": "lens_",
                },
                "Aperture_yhw": {
                    "f": ui.input_text,
                    "value": yhw,
                    "label": "Y-Half Width",
                    "prefix": "lens_",
                },
                "Aperture_xdecenter": {
                    "f": ui.input_text,
                    "value": xdecenter,
                    "label": "X-Decenter",
                    "prefix": "lens_",
                },
                "Aperture_ydecenter": {
                    "f": ui.input_text,
                    "value": ydecenter,
                    "label": "Y-Decenter",
                    "prefix": "lens_",
                },
            },
        }
        lens_elems[n]["Par1"] = {
            "f": ui.input_text,
            "value": item.get("par1", ""),
            "width": 1,
            "prefix": "lens_",
            "placeholder": Placeholder["Par1"][surface_type],
        }
        lens_elems[n]["Par2"] = {
            "f": ui.input_text,
            "value": item.get("par2", ""),
            "width": 1,
            "prefix": "lens_",
            "placeholder": Placeholder["Par2"][surface_type],
        }
        lens_elems[n]["Par3"] = {
            "f": ui.input_text,
            "value": item.get("par3", ""),
            "width": 1,
            "prefix": "lens_",
            "placeholder": Placeholder["Par3"][surface_type],
        }
        lens_elems[n]["Par4"] = {
            "f": ui.input_text,
            "value": item.get("par4", ""),
            "width": 1,
            "prefix": "lens_",
            "placeholder": Placeholder["Par4"][surface_type],
        }
        lens_elems[n]["Par5"] = {
            "f": ui.input_text,
            "value": item.get("par5", ""),
            "width": 1,
            "prefix": "lens_",
            "placeholder": Placeholder["Par5"][surface_type],
        }
        lens_elems[n]["Par6"] = {
            "f": ui.input_text,
            "value": item.get("par6", ""),
            "width": 1,
            "prefix": "lens_",
            "placeholder": Placeholder["Par6"][surface_type],
        }
        lens_elems[n]["Par7"] = {
            "f": ui.input_text,
            "value": item.get("par7", ""),
            "width": 1,
            "prefix": "lens_",
            "placeholder": Placeholder["Par7"][surface_type],
        }
        lens_elems[n]["Par8"] = {
            "f": ui.input_text,
            "value": item.get("par8", ""),
            "width": 1,
            "prefix": "lens_",
            "placeholder": Placeholder["Par8"][surface_type],
        }

    zernike_elems = {}
    for key in config.sections():
        if not key.startswith("lens_"):
            continue
        item = config[key]
        if not item.get("surfacetype") == "Zernike":
            continue

        n = int(key.split("_")[1])
        zernike_elems[n] = {}

        zindex = item.get("zindex", "").split(",")
        zcoeff = item.get("z", "").split(",")

        ordering = item.get("par2")
        azimuthal, radial = Zernike.j2mn(N=len(zindex), ordering=ordering)

        for zi, zc in zip(zindex, zcoeff):
            zernike_elems[n][zi] = {}
            zernike_elems[n][zi]["n"] = {
                "f": ui.p,
                "width": 3,
                "value": radial[int(zi)],
            }
            zernike_elems[n][zi]["m"] = {
                "f": ui.p,
                "width": 3,
                "value": azimuthal[int(zi)],
            }
            zernike_elems[n][zi]["Zindex"] = {
                "f": ui.p,
                "width": 3,
                "value": zi,
            }
            zernike_elems[n][zi]["Zcoeff"] = {
                "f": ui.input_text,
                "width": 3,
                "value": zc,
                "prefix": f"lens_{n}_",
            }

    zernike_sidebar_elems = []
    zernike_tab_elems = []
    if zernike_elems:
        zernike_choices = [f"S{n}" for n in zernike_elems]

        zernike_sidebar_elems = [
            *[
                ui.input_select(
                    id=f"select_{name}", label=f"Select {name}", choices=choice
                )
                for name, choice in zip(["Zernike"], [zernike_choices])
            ],
        ]
        zernike_tab_elems = [
            ui.layout_column_wrap(
                ui.card(
                    ui.card_header("Explorer"),
                    ui.card_body(
                        output_text_verbatim("zernike_inputs"),
                        nested_div("zernike"),
                    ),
                    max_height="45vw",
                ),
                ui.card(
                    ui.card_header("Plot"),
                    ui.card_footer(
                        ui.input_action_button(
                            "do_plot_zernike",
                            "Run",
                            icon=ICONS["run"],
                            class_="btn-success",
                        ),
                        ui.input_action_button(
                            "download_plot_zernike",
                            "Save",
                            icon=ICONS["save"],
                        ),
                    ),
                    ui.card_body(
                        output_text_verbatim("plot_zernike_inputs"),
                        ui.output_plot("plot_zernike"),
                    ),
                    min_height="45vw",
                ),
            ),
        ]

    psd_elems = {}
    for key in config.sections():
        if not key.startswith("lens_"):
            continue
        item = config[key]
        if not item.get("surfacetype") == "PSD":
            continue

        n = int(key.split("_")[1])
        psd_elems[n] = {}
        psd_elems[n][0] = {}

        A = float(item.get("Par1"))
        B = float(item.get("Par2"))
        C = float(item.get("Par3"))
        fknee = float(item.get("Par4"))
        fmin = float(item.get("Par5"))
        fmax = float(item.get("Par6"))
        SR = item.get("Par7")
        units = item.get("Par8")
        sfe_rms = PSD.sfe_rms(A, B, C, fknee, fmin, fmax)

        psd_elems[n][0]["PSD SFE RMS"] = {
            "f": ui.p,
            "width": 2,
            "value": f"{sfe_rms:.3f}",
        }
        psd_elems[n][0]["SR RMS"] = {
            "f": ui.p,
            "width": 2,
            "value": f"{SR}",
        }
        psd_elems[n][0]["SFE units"] = {
            "f": ui.p,
            "width": 2,
            "value": f"{units}",
        }

    psd_sidebar_elems = []
    psd_tab_elems = []
    if psd_elems:
        psd_choices = [f"S{n}" for n in psd_elems]

        psd_sidebar_elems = [
            *[
                ui.input_select(
                    id=f"select_{name}", label=f"Select {name}", choices=choice
                )
                for name, choice in zip(["PSD"], [psd_choices])
            ],
        ]
        psd_tab_elems = [
            ui.layout_column_wrap(
                ui.card(
                    ui.card_header("Explorer"),
                    ui.card_body(
                        output_text_verbatim("psd_inputs"),
                        output_text_verbatim("psd_output"),
                        nested_div("PSD"),
                    ),
                    ui.card_footer(
                        ui.tags.div(
                            ui.input_action_button(
                                "calc_PSD",
                                "Run",
                                icon=ICONS["run"],
                                class_="btn-success",
                            ),
                        ),
                    ),
                    max_height="45vh",
                ),
                ui.card(
                    ui.card_header("Plot"),
                    ui.card_footer(
                        ui.input_action_button(
                            "do_plot_PSD",
                            "Run",
                            icon=ICONS["run"],
                            class_="btn-success",
                        ),
                        ui.input_action_button(
                            "download_plot_PSD",
                            "Save",
                            icon=ICONS["save"],
                        ),
                    ),
                    ui.card_body(
                        output_text_verbatim("plot_psd_inputs"),
                        ui.output_plot("plot_PSD"),
                    ),
                    min_height="45vw",
                ),
            ),
        ]

    gridsag_elems = {}
    for key in config.sections():
        if not key.startswith("lens_"):
            continue
        item = config[key]
        if not item.get("surfacetype") == "Grid Sag":
            continue

        n = int(key.split("_")[1])
        gridsag_elems[n] = {}
        gridsag_elems[n][0] = {}

        filename = item.get("Par8")

        gridsag_elems[n][0]["Filename"] = {
            "f": ui.p,
            "width": 2,
            "value": f"{filename}",
        }

    gridsag_sidebar_elems = []
    gridsag_tab_elems = []
    if gridsag_elems:
        gridsag_choices = [f"S{n}" for n in gridsag_elems]

        gridsag_sidebar_elems = [
            *[
                ui.input_select(
                    id=f"select_{name}", label=f"Select {name}", choices=choice
                )
                for name, choice in zip(["gridsag"], [gridsag_choices])
            ],
        ]

        gridsag_tab_elems = [
            ui.layout_column_wrap(
                ui.card(
                    ui.card_header("Explorer"),
                    ui.card_body(
                        output_text_verbatim("gridsag_inputs"),
                        output_text_verbatim("gridsag_output"),
                        nested_div("gridsag"),
                    ),
                    max_height="45vh",
                ),
                ui.card(
                    ui.card_header(
                        "Plot",
                    ),
                    ui.card_footer(
                        ui.input_action_button(
                            "do_plot_gridsag",
                            "Run",
                            icon=ICONS["run"],
                            class_="btn-success",
                        ),
                        ui.input_action_button(
                            "download_plot_gridsag", "Save", icon=ICONS["save"]
                        ),
                    ),
                    ui.card_body(
                        output_text_verbatim("plot_gridsag_inputs"),
                        ui.output_plot("plot_gridsag"),
                    ),
                    min_height="45vw",
                ),
            ),
        ]

    wfe_elems = (
        zernike_sidebar_elems,
        zernike_elems,
        zernike_tab_elems,
        psd_sidebar_elems,
        psd_elems,
        psd_tab_elems,
        gridsag_sidebar_elems,
        gridsag_elems,
        gridsag_tab_elems,
    )

    surface_choices = [
        f"S{key}" for key, item in lens_elems.items() if item["Save"]["value"]
    ]

    wl_choices = [f"w{n}" for n in wl_elems]
    field_choices = [f"f{n}" for n in field_elems]

    analysis_sidebar_elems = [
        *[
            ui.input_select(id=f"select_{name}", label=f"Select {name}", choices=choice)
            for name, choice in zip(["field", "wl"], [field_choices, wl_choices])
        ],
    ]

    analysis_elems = [
        ui.layout_column_wrap(
            ui.navset_card_tab(
                ui.nav_panel(
                    "Fresnel POP",
                    ui.card(
                        ui.card_body(
                            output_text_verbatim("pop_inputs"),
                            output_text_verbatim("pop_output"),
                        ),
                        ui.card_footer(
                            ui.tags.div(
                                ui.input_action_button(
                                    "calc_pop",
                                    "Run",
                                    icon=ICONS["run"],
                                    class_="btn-success",
                                ),
                                ui.input_action_button(
                                    "download_pop", "Save", icon=ICONS["save"]
                                ),
                            ),
                        ),
                        max_height="45vh",
                    ),
                ),
                ui.nav_panel(
                    "Ray Tracing",
                    ui.card(
                        ui.card_body(
                            output_text_verbatim("raytrace_inputs"),
                            output_text_verbatim("raytrace_output"),
                        ),
                        ui.card_footer(
                            ui.tags.div(
                                ui.input_action_button(
                                    "calc_raytrace",
                                    "Run",
                                    icon=ICONS["run"],
                                    class_="btn-success",
                                ),
                                ui.input_action_button(
                                    "download_raytrace", "Save", icon=ICONS["save"]
                                ),
                            ),
                        ),
                        max_height="45vh",
                    ),
                ),
            ),
            ui.card(
                ui.card_header(
                    ui.tags.div(
                        "Plot",
                        ui.popover(
                            ICONS["gear"],
                            *[
                                ui.input_select(
                                    id="plot_select_surface",
                                    label="Select surface",
                                    choices=surface_choices,
                                    selected=surface_choices[-1],
                                ),
                                ui.input_select(
                                    id="plot_select_scale",
                                    label="Select scale",
                                    choices=["log", "linear"],
                                ),
                                ui.input_text(
                                    id="plot_select_zoom",
                                    label="Select zoom",
                                    value=1.0,
                                ),
                                ui.input_checkbox(
                                    id="plot_select_dark_rings",
                                    label="Dark rings",
                                    value=True,
                                ),
                            ],
                            title="Settings",
                            placement="top",
                        ),
                        class_=CARD_HEADER_CLASS,
                    ),
                ),
                ui.card_footer(
                    ui.tags.div(
                        ui.input_action_button(
                            "do_plot",
                            "Run",
                            icon=ICONS["run"],
                            class_="btn-success",
                        ),
                        ui.input_action_button(
                            "download_plot", "Save", icon=ICONS["save"]
                        ),
                    ),
                ),
                ui.card_body(
                    output_text_verbatim("plot_inputs"),
                    ui.output_plot("plot"),
                ),
                min_height="45vw",
            ),
            fillable=False,
        ),
    ]

    units_elems = []

    return (
        general_elems,
        field_elems,
        wl_elems,
        lens_elems,
        wfe_elems,
        analysis_sidebar_elems,
        analysis_elems,
        units_elems,
    )
