from shiny import ui

from paos import Zernike

from .shared import ellipsis
from .shared import output_text_verbatim
from .shared import ICONS
from .shared import card_header_class_
from .shared import nested_div


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
    ]

    units_elems = [
        ui.p("Lens: ", config["general"].get("lens_unit", "m")),
        ui.p("Angle: ", config["general"].get("angle_unit", "degrees")),
        ui.p(
            "Wavelength: ",
            config["general"].get("wavelength_units", "micrometers"),
        ),
        ui.p("Temperature: ", config["general"].get("temperature_units", "C")),
        ui.p("Pressure: ", config["general"].get("pressure_units", "atm")),
    ]

    sim_elems = [
        ui.input_text(
            "grid_size",
            "Grid size",
            value=config["general"].getint("grid_size", "512"),
        ),
        ui.input_text("zoom", "Zoom", value=config["general"].getint("zoom", "4")),
        ui.input_text(
            "tambient",
            "Ambient temperature",
            value=config["general"].getfloat("tambient", "20.0"),
        ),
        ui.input_text(
            "pambient",
            "Ambient pressure",
            value=config["general"].getfloat("pambient", "1.0"),
        ),
    ]

    field_elems = {}
    for n, (key, value) in enumerate(config.items("fields")):
        n += 1
        field_elems[n] = {}
        field_elems[n]["Number"] = {
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
    field_choices = [f"f{n}" for n in field_elems]

    wl_elems = {}
    for n, (key, value) in enumerate(config.items("wavelengths")):
        n += 1
        wl_elems[n] = {}
        wl_elems[n]["Number"] = {
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
    wl_choices = [f"w{n}" for n in wl_elems]

    lens_elems = {}
    for key in config.sections():
        if not key.startswith("lens_"):
            continue
        n = int(key.split("_")[1])
        item = config[key]

        lens_elems[n] = {}
        lens_elems[n]["Number"] = {
            "f": ui.p,
            "width": 1,
            "value": n,
        }
        lens_elems[n]["SurfaceType"] = {
            "f": ui.input_select,
            "choices": [
                "INIT",
                "Coordinate Break",
                "Standard",
                "Paraxial Lens",
                "ABCD",
                "Zernike",
                "PSD",
            ],
            "width": 1,
            "selected": item.get("surfacetype"),
            "prefix": "lens_",
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
            "f": ui.accordion,
            "width": 2,
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
        }
        lens_elems[n]["Par2"] = {
            "f": ui.input_text,
            "value": item.get("par2", ""),
            "width": 1,
            "prefix": "lens_",
        }
        lens_elems[n]["Par3"] = {
            "f": ui.input_text,
            "value": item.get("par3", ""),
            "width": 1,
            "prefix": "lens_",
        }
        lens_elems[n]["Par4"] = {
            "f": ui.input_text,
            "value": item.get("par4", ""),
            "width": 1,
            "prefix": "lens_",
        }
        lens_elems[n]["Par5"] = {
            "f": ui.input_text,
            "value": item.get("par5", ""),
            "width": 1,
            "prefix": "lens_",
        }
        lens_elems[n]["Par6"] = {
            "f": ui.input_text,
            "value": item.get("par6", ""),
            "width": 1,
            "prefix": "lens_",
        }
        lens_elems[n]["Par7"] = {
            "f": ui.input_text,
            "value": item.get("par7", ""),
            "width": 1,
            "prefix": "lens_",
        }
        lens_elems[n]["Par8"] = {
            "f": ui.input_text,
            "value": item.get("par8", ""),
            "width": 1,
            "prefix": "lens_",
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

    if zernike_elems:
        zernike_choices = [f"S{n}" for n in zernike_elems]
        zernike_explorer_elems = [
            ui.card_header(
                "Zernike Explorer",
                ui.popover(
                    ICONS["ellipsis"],
                    *[
                        ui.input_select(
                            id="zernike_select_surface",
                            label="Choose surface",
                            choices=zernike_choices,
                            selected=zernike_choices[0],
                        ),
                    ],
                    title="",
                    placement="top",
                ),
                class_=card_header_class_,
            ),
            output_text_verbatim("zernike_inputs"),
            nested_div("zernike"),
            ui.card_footer(),
        ]
        zernike_plots_elems = [
            ui.card_header(
                "Zernike Errormap",
                ui.popover(
                    ICONS["ellipsis"],
                    *[
                        ui.input_select(
                            id="zernike_plot_select_surface",
                            label="Choose surface",
                            choices=zernike_choices,
                            selected=zernike_choices[0],
                        ),
                    ],
                    title="",
                    placement="top",
                ),
                class_=card_header_class_,
            ),
            output_text_verbatim("plot_zernike_inputs"),
            ui.output_plot("plot_zernike"),
            ui.card_footer(
                ui.input_action_button("do_plot_zernike", "Run", icon=ICONS["run"]),
                ui.input_action_button(
                    "download_plot_zernike", "Download", icon=ICONS["save"]
                ),
            ),
        ]

    else:
        zernike_explorer_elems = []
        zernike_plots_elems = []

    pop_elems = [
        ui.card_header(
            "Fresnel POP",
            ellipsis(
                "pop",
                names=["field", "wl"],
                choices=[field_choices, wl_choices],
            ),
            class_=card_header_class_,
        ),
        output_text_verbatim("pop_inputs"),
        output_text_verbatim("pop_output"),
        ui.card_footer(
            ui.input_action_button("calc_pop", "Run", icon=ICONS["run"]),
            ui.input_action_button("download_pop", "Download", icon=ICONS["save"]),
        ),
    ]

    raytrace_elems = [
        ui.card_header(
            "Ray Tracing",
            ellipsis(
                "raytrace",
                names=["field", "wl"],
                choices=[field_choices, wl_choices],
            ),
            class_=card_header_class_,
        ),
        output_text_verbatim("raytrace_inputs"),
        output_text_verbatim("raytrace_output"),
        ui.card_footer(
            ui.input_action_button("calc_raytrace", "Run", icon=ICONS["run"]),
            ui.input_action_button("download_raytrace", "Download", icon=ICONS["save"]),
        ),
    ]

    surface_choices = [f"S{n}" for n in lens_elems if lens_elems[n]["Save"]["value"]]
    plots_elems = [
        ui.card_header(
            "Plots",
            ui.popover(
                ICONS["ellipsis"],
                *[
                    ui.input_select(
                        id="plot_select_surface",
                        label="Choose surface",
                        choices=surface_choices,
                        selected=surface_choices[-1],
                    ),
                    ui.input_select(
                        id="plot_select_scale",
                        label="Choose scale",
                        choices=["log", "linear"],
                    ),
                    ui.input_text(
                        id="plot_select_zoom",
                        label="Choose zoom",
                        value=1.0,
                    ),
                    ui.input_checkbox(
                        id="plot_select_dark_rings",
                        label="Dark rings",
                        value=True,
                    ),
                ],
                title="",
                placement="top",
            ),
            class_=card_header_class_,
        ),
        output_text_verbatim("plot_inputs"),
        ui.output_plot("plot"),
        ui.card_footer(
            ui.input_action_button("do_plot", "Run", icon=ICONS["run"]),
            ui.input_action_button("download_plot", "Download", icon=ICONS["save"]),
        ),
    ]

    return (
        general_elems,
        units_elems,
        sim_elems,
        field_elems,
        wl_elems,
        lens_elems,
        zernike_explorer_elems,
        zernike_elems,
        zernike_plots_elems,
        pop_elems,
        raytrace_elems,
        plots_elems,
    )
