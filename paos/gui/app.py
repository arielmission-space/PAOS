import os
import time
import configparser
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

from htmltools import Tag
from starlette.requests import Request as StarletteRequest

from shiny import App
from shiny import render
from shiny import ui
from shiny import reactive
from shiny import req
from shiny.types import FileInfo

import paos
from paos import logger
from paos import __pkg_name__
from paos import __version__
from paos import __author__
from paos import __license__
from paos.core.parseConfig import parse_config

from paos.gui.core.io import to_ini
from paos.gui.core.elems import app_elems
from paos.gui.core.plot import simple_plot
from paos.gui.core.plot import Zernike_plot
from paos.gui.core.plot import PSD_plot
from paos.gui.core.plot import gridsag_plot
from paos.gui.core.shared import nested_div
from paos.gui.core.shared import menu_panel
from paos.gui.core.shared import refresh_ui
from paos.gui.core.shared import modal_download


def app_ui(request: StarletteRequest) -> Tag:
    """
    Returns the UI for the PAOS application.

    It generates the UI using Shiny's ui.page_fillable function.
    It includes a page navbar with a nav spacer and a nav panel.

    Returns:
        Tag: The UI for the PAOS application.
    """
    return ui.page_fillable(
        # ui.tags.script(
        # """
        # Shiny.addCustomMessageHandler('refresh', function(message) {
        #     window.location.reload();
        # });
        # """,
        # ),
        ui.page_navbar(
            ui.nav_spacer(),
            ui.nav_panel(
                "System Explorer",
                ui.card(
                    ui.layout_sidebar(
                        ui.sidebar(
                            nested_div("general"),
                            nested_div("sim"),
                            title="Settings",
                            width="20vw",
                        ),
                        ui.card(
                            ui.layout_column_wrap(
                                nested_div("wl"),
                                nested_div("field"),
                            ),
                            fill=False,
                        ),
                    ),
                    min_height="75vh",
                    max_height="75vh",
                ),
            ),
            ui.nav_panel(
                "Lens Editor",
                ui.card(
                    nested_div("lens"),
                    max_height="75vh",
                    min_height="75vh",
                ),
            ),
            ui.nav_panel(
                "Wavefront Editor",
                ui.card(
                    ui.navset_card_tab(
                        ui.nav_spacer(),
                        ui.nav_panel(
                            "Zernike",
                            ui.layout_sidebar(
                                ui.sidebar(
                                    nested_div("Zernike_settings"),
                                    title="Settings",
                                    width="15vw",
                                ),
                                nested_div("Zernike_tab"),
                            ),
                        ),
                        ui.nav_panel(
                            "PSD",
                            ui.layout_sidebar(
                                ui.sidebar(
                                    nested_div("PSD_settings"),
                                    title="Settings",
                                    width="15vw",
                                ),
                                nested_div("PSD_tab"),
                            ),
                        ),
                        ui.nav_panel(
                            "Grid Sag",
                            ui.layout_sidebar(
                                ui.sidebar(
                                    nested_div("gridsag_settings"),
                                    title="Settings",
                                    width="15vw",
                                ),
                                nested_div("gridsag_tab"),
                            ),
                        ),
                        ui.nav_spacer(),
                    ),
                    max_height="75vh",
                    min_height="75vh",
                ),
            ),
            ui.nav_panel(
                "Optical Analysis",
                ui.card(
                    ui.layout_sidebar(
                        ui.sidebar(
                            nested_div("analysis_settings"),
                            title="Settings",
                            width="15vw",
                        ),
                        nested_div("analysis"),
                    ),
                    max_height="75vh",
                    min_height="75vh",
                ),
            ),
            id="navbar",
            title=ui.tags.div(
                ui.tags.a(
                    ui.tags.img(src="static/logo.png", height="50px"),
                    # href="https://github.com/arielmission-space/PAOS",
                ),
                ui.input_dark_mode(id="dark_mode", mode="light"),
                id="logo-top",
                class_="navigation-logo",
            ),
            header=ui.page_navbar(
                [
                    ui.nav_menu(
                        "File",
                        menu_panel("open"),
                        menu_panel("save"),
                        menu_panel("close"),
                    ),
                    ui.nav_menu(
                        "Help",
                        menu_panel("docs"),
                        menu_panel("about"),
                    ),
                ],
            ),
            footer=ui.panel_well(
                ui.p(
                    f"{__pkg_name__} v{__version__}; {__author__}",
                ),
            ),
            window_title=f"{__pkg_name__} GUI",
            selected="Wavefront Editor",
        ),
        gap="2px",
        padding="2px",
    )


def server(input, output, session):
    ini_file = reactive.value("filename")
    config = reactive.value(configparser.ConfigParser())
    retval = reactive.value({})
    figure = reactive.value(None)
    figure_zernike = reactive.value(None)
    figure_PSD = reactive.value(None)
    figure_gridsag = reactive.value(None)

    for file in os.listdir(cache):
        os.remove(os.path.join(cache, file))

    @reactive.effect
    @reactive.event(
        input.save,
        input.calc_raytrace,
        input.calc_pop,
        input.calc_PSD,
        input.do_plot_zernike,
    )
    def _():
        req(input.calc_raytrace)
        req(input.calc_pop)
        req(input.calc_PSD)
        req(input.do_plot_zernike)
        to_ini(input=input, config=config, tmp=cache / "tmp.ini")

    @reactive.calc
    def calc_raytrace():
        req(config.get().sections())
        req(input.select_field())
        req(input.select_wl())

        field = input.select_field()
        wl = input.select_wl()

        field_idx = int(field[1:]) - 1
        wl_idx = int(wl[1:]) - 1

        _, _, _, fields, opt_chains = parse_config(cache / "tmp.ini")

        with ui.Progress(min=1, max=15) as p:
            p.set(message="Calculation in progress", detail="")
            raytrace = paos.raytrace(fields[field_idx], opt_chains[wl_idx])

            p.set(15, message="Raytrace complete!", detail="")
            time.sleep(1.0)

        return "\n".join(raytrace)

    @reactive.effect
    @reactive.event(input.download_raytrace)
    def download_raytrace():
        req(input.calc_raytrace())
        req(input.download_raytrace())
        req(config.get().sections())
        modal_download("raytrace", "txt")

    @render.download
    def download_raytrace_txt():
        raytrace: str = calc_raytrace()
        outfile: list[FileInfo] | None = input.save_txt()
        logger.info(f"Downloaded {outfile}")

        with open(cache / outfile, "w", encoding="utf-8") as f:
            f.write(raytrace)

        return os.path.join(os.path.dirname(__file__), "cache", outfile)

    @render.text
    @reactive.event(input.calc_raytrace)
    def raytrace_inputs():
        req(input.calc_raytrace())

        refresh_ui(
            "raytrace_inputs",
            [ui.output_text_verbatim("raytrace_inputs", placeholder=True)],
        )

        field = input.select_field()
        wl = input.select_wl()

        return f"Field: {field}, Wavelength: {wl}"

    @render.text
    @reactive.event(input.calc_raytrace)
    def raytrace_output():
        req(input.calc_raytrace())

        refresh_ui(
            "raytrace_output",
            [ui.output_text_verbatim("raytrace_output", placeholder=True)],
        )

        return calc_raytrace()

    @reactive.calc
    def calc_pop():
        req(config.get().sections())
        req(input.select_field())
        req(input.select_wl())

        field = input.select_field()
        wl = input.select_wl()

        field_idx = int(field[1:]) - 1
        wl_idx = int(wl[1:]) - 1

        pup_diameter, parameters, wavelengths, fields, opt_chains = parse_config(
            cache / "tmp.ini"
        )

        with ui.Progress(min=1, max=15) as p:
            p.set(message="Calculation in progress", detail="")
            retval.set(
                paos.run(
                    pup_diameter,
                    1.0e-6 * wavelengths[wl_idx],
                    parameters["grid_size"],
                    parameters["zoom"],
                    fields[field_idx],
                    opt_chains[wl_idx],
                )
            )

            p.set(15, message="POP complete!", detail="")
            time.sleep(1.0)

        return "POP output available: try plotting it!"

    @reactive.effect
    @reactive.event(input.download_pop)
    def download_pop():
        req(input.calc_pop())
        req(input.download_pop())
        req(config.get().sections())
        modal_download("pop", "h5")

    @render.download
    def download_pop_h5():
        outfile: list[FileInfo] | None = input.save_h5()

        paos.save_output(
            retval.get(),
            str(cache / outfile),
            keys_to_keep=["amplitude", "dx", "dy", "wl"],
        )

        return os.path.join(os.path.dirname(__file__), "cache", outfile)

    @render.text
    @reactive.event(input.calc_pop)
    def pop_inputs():
        req(input.calc_pop())

        refresh_ui(
            "pop_inputs",
            [ui.output_text_verbatim("pop_inputs", placeholder=True)],
        )

        field = input.select_field()
        wl = input.select_wl()

        return f"Field: {field}, Wavelength: {wl}"

    @render.text
    @reactive.event(input.calc_pop)
    def pop_output():
        req(input.calc_pop())

        refresh_ui(
            "pop_output",
            [ui.output_text_verbatim("pop_output", placeholder=True)],
        )

        return calc_pop()

    @render.plot(alt="PSF plot")
    @reactive.event(input.do_plot)
    def plot():
        req(input.do_plot())
        req(input.calc_pop())
        req(input.plot_select_surface())
        req(input.plot_select_scale())
        req(input.plot_select_zoom())

        surface = int(input.plot_select_surface()[1:])
        scale = input.plot_select_scale()
        zoom = input.plot_select_zoom()
        dark_rings = input.plot_select_dark_rings()

        fig, ax = plt.subplots()
        simple_plot(
            fig=fig,
            axis=ax,
            key=surface,
            item=retval.get()[surface],
            ima_scale=scale,
            options={
                surface: {
                    "surface_zoom": float(zoom),
                    "dark_rings": bool(dark_rings),
                }
            },
        )

        figure.set(fig)

        return fig

    @reactive.effect
    @reactive.event(input.download_plot)
    def download_plot():
        req(input.do_plot())
        req(input.download_plot())
        req(config.get().sections())
        req(retval.get())
        modal_download("plot", "pdf")

    @render.download
    def download_plot_pdf():
        outfile: list[FileInfo] | None = input.save_pdf()

        figure.get().savefig(cache / outfile)

        return os.path.join(os.path.dirname(__file__), "cache", outfile)

    @render.text
    @reactive.event(input.do_plot)
    def plot_inputs():
        req(input.do_plot())

        refresh_ui(
            "plot_inputs",
            [ui.output_text_verbatim("plot_inputs", placeholder=True)],
        )

        surface = input.plot_select_surface()
        scale = input.plot_select_scale()
        zoom = input.plot_select_zoom()
        dark_rings = input.plot_select_dark_rings()

        return f"Surface: {surface}, Scale: {scale}, Zoom: {zoom}, Dark Rings: {dark_rings}"

    @reactive.effect
    @reactive.event(input.save)
    def save():
        req(config.get().sections())
        modal_download("config", "ini")

    @render.download
    def download_config_ini():
        outfile: list[FileInfo] | None = input.save_ini()

        with open(cache / "tmp.ini", "r", encoding="utf-8") as f:
            with open(cache / outfile, "w", encoding="utf-8") as cf:
                cf.write(f.read())

        return os.path.join(os.path.dirname(__file__), "cache", outfile)

    @reactive.effect
    @reactive.event(input.about)
    def about():
        req(input.about())
        m = ui.modal(
            ui.markdown(
                f"SOFTWARE: {__pkg_name__} v{__version__}  \n"
                f"AUTHOR: {__author__}  \n"
                f"LICENSE: {__license__}  \n"
            ),
            title="About",
            easy_close=True,
        )
        ui.modal_show(m)

    @reactive.effect
    @reactive.event(input.docs)
    def docs():
        req(input.docs())
        m = ui.modal(
            ui.markdown(
                f"Click [here](https://paos.readthedocs.io/en/latest/) to access the {__pkg_name__} documentation."
            ),
            title="Documentation",
            easy_close=True,
        )
        ui.modal_show(m)

    @reactive.effect
    @reactive.event(input.open)
    def _():
        req(input.open())
        m = ui.modal(
            ui.input_file(
                id="open_ini",
                label=ui.markdown(
                    "Input files must be in the INI format.  \n"
                    f"Example files can be found in the {__pkg_name__} \n"
                    "public [GitHub](https://github.com/arielmission-space/PAOS) repository."
                ),
                accept=[".ini"],
                multiple=False,
                button_label="Browse",
            ),
            title="Open INI File",
            easy_close=True,
            footer=ui.markdown(
                "Note: you may only open one file per session.  \n"
                "Refresh the page to open a different file."
            ),
        )
        ui.modal_show(m)

    @render.text
    @reactive.event(input.open_ini, input.select_Zernike)
    def Zernike_inputs():
        req(config.get().sections())
        req(input.select_Zernike())

        refresh_ui(
            "Zernike_inputs",
            [ui.output_text_verbatim("Zernike_inputs", placeholder=True)],
        )

        surface = input.select_Zernike()

        wfe_elems = app_elems(config.get())[5]
        Zernike_elems = wfe_elems[1]

        surface_key = int(surface[1:])
        refresh_ui("zernike", Zernike_elems, mode="nested-dict", key=surface_key)

        return f"Surface: {surface}"

    @render.text
    @reactive.event(input.do_plot_zernike)
    def plot_Zernike_inputs():
        req(input.do_plot_zernike())

        refresh_ui(
            "plot_Zernike_inputs",
            [ui.output_text_verbatim("plot_Zernike_inputs", placeholder=True)],
        )

        surface = input.select_Zernike()

        return f"Surface: {surface}"

    @render.plot(alt="Zernike plot")
    @reactive.event(input.do_plot_zernike)
    def plot_zernike():
        req(input.do_plot_zernike())
        req(input.select_Zernike())
        req(config.get().sections())

        surface = input.select_Zernike()
        surface_key = int(surface[1:])
        Zernike_section = f"lens_{surface_key:02d}"
        Zernike_section = config.get()[Zernike_section]

        zindex = Zernike_section.get("zindex").split(",")
        zindex = list(map(int, zindex))
        zcoeffs = Zernike_section.get("z").split(",")
        zcoeffs = list(map(float, zcoeffs))
        wavelength = float(Zernike_section.get("par1"))
        ordering = Zernike_section.get("par2")
        normalize = bool(Zernike_section.get("par3"))
        orthonorm = bool(Zernike_section.get("par6"))

        fig, ax = plt.subplots()
        Zernike_plot(
            fig=fig,
            axis=ax,
            surface=surface,
            index=zindex,
            Z=zcoeffs,
            wavelength=wavelength,
            ordering=ordering,
            normalize=normalize,
            orthonorm=orthonorm,
            grid_size=int(input.grid_size()),
        )

        figure_zernike.set(fig)

        return fig

    @reactive.effect
    @reactive.event(input.download_plot_zernike)
    def download_plot_zernike():
        req(config.get().sections())
        req(input.do_plot_zernike())
        modal_download("plot_zernike", "pdf")

    @render.download
    def download_plot_Zernike_pdf():
        outfile: list[FileInfo] | None = input.save_pdf()

        figure_zernike.get().savefig(cache / outfile)

        return os.path.join(os.path.dirname(__file__), "cache", outfile)

    @reactive.calc
    def calc_PSD():
        req(config.get().sections())
        req(input.select_PSD())

        surface = input.select_PSD()

        wfe_elems = app_elems(config.get())[5]
        PSD_elems = wfe_elems[4]

        surface_key = int(surface[1:])
        refresh_ui("PSD", PSD_elems, mode="nested-dict", key=surface_key)

        return f"Stats for Surface: {surface}"

    @render.text
    @reactive.event(input.open_ini, input.select_PSD)
    def PSD_inputs():
        req(input.select_PSD())

        refresh_ui(
            "PSD_inputs",
            [ui.output_text_verbatim("PSD_inputs", placeholder=True)],
        )

        surface = input.select_PSD()

        return f"Surface: {surface}"

    @render.text
    @reactive.event(input.calc_PSD)
    def PSD_output():
        req(input.calc_PSD())

        refresh_ui(
            "PSD_output",
            [ui.output_text_verbatim("PSD_output", placeholder=True)],
        )

        return calc_PSD()

    @render.text
    @reactive.event(input.do_plot_PSD)
    def plot_PSD_inputs():
        req(input.do_plot_PSD())

        refresh_ui(
            "plot_PSD_inputs",
            [ui.output_text_verbatim("plot_PSD_inputs", placeholder=True)],
        )

        surface = input.select_PSD()

        return f"Surface: {surface}"

    @render.plot(alt="PSD plot")
    @reactive.event(input.do_plot_PSD)
    def plot_PSD():
        req(input.do_plot_PSD())
        req(input.select_PSD())
        req(config.get().sections())

        surface = input.select_PSD()
        surface_key = int(surface[1:])
        PSD_section = f"lens_{surface_key:02d}"
        PSD_section = config.get()[PSD_section]

        A = float(PSD_section.get("par1"))
        B = float(PSD_section.get("par2"))
        C = float(PSD_section.get("par3"))
        fknee = float(PSD_section.get("par4"))
        fmin = float(PSD_section.get("par5"))
        fmax = float(PSD_section.get("par6"))
        SR = float(PSD_section.get("par7"))
        units = PSD_section.get("par8")
        phi = float(input.PSD_plot_phi())

        fig, ax = plt.subplots()
        PSD_plot(
            fig=fig,
            axis=ax,
            surface=surface,
            A=A,
            B=B,
            C=C,
            fknee=fknee,
            fmin=fmin,
            fmax=fmax,
            SR=SR,
            units=units,
            grid_size=int(input.grid_size()),
            phi=phi,
        )

        figure_PSD.set(fig)

        return fig

    @reactive.effect
    @reactive.event(input.download_plot_PSD)
    def download_plot_PSD():
        req(config.get().sections())
        req(input.do_plot_PSD())
        modal_download("plot_PSD", "pdf")

    @render.download
    def download_plot_PSD_pdf():
        outfile: list[FileInfo] | None = input.save_pdf()

        figure_PSD.get().savefig(cache / outfile)

        return os.path.join(os.path.dirname(__file__), "cache", outfile)

    @render.text
    @reactive.event(input.open_ini, input.select_gridsag)
    def gridsag_inputs():
        req(input.select_gridsag())

        refresh_ui(
            "gridsag_inputs",
            [ui.output_text_verbatim("gridsag_inputs", placeholder=True)],
        )

        surface = input.select_gridsag()

        return f"Surface: {surface}"

    @render.text
    @reactive.event(input.do_plot_gridsag)
    def plot_gridsag_inputs():
        req(input.do_plot_gridsag())

        refresh_ui(
            "plot_gridsag_inputs",
            [ui.output_text_verbatim("plot_gridsag_inputs", placeholder=True)],
        )

        surface = input.select_gridsag()

        return f"Surface: {surface}"

    @render.plot(alt="Grid Sag plot")
    @reactive.event(input.do_plot_gridsag)
    def plot_gridsag():
        req(input.do_plot_gridsag())
        req(input.select_gridsag())
        req(config.get().sections())

        surface = input.select_gridsag()
        surface_key = int(surface[1:])
        gridsag_section = f"lens_{surface_key:02d}"
        gridsag_section = config.get()[gridsag_section]

        wave = 1.0e-6 * float(gridsag_section.get("Par1"))
        grid_sag_path = gridsag_section.get("Par8")

        with open(grid_sag_path, "rb") as f:
            grid_sag = np.load(f, allow_pickle=True).item()

        grid_sag_mask = grid_sag.get("mask", False)
        grid_sag = np.ma.MaskedArray(
            grid_sag["data"], mask=grid_sag_mask | np.isinf(grid_sag["data"])
        )
        grid_sag *= wave

        fig, ax = plt.subplots()
        gridsag_plot(
            fig=fig,
            axis=ax,
            surface=surface,
            data=grid_sag,
        )

        figure_gridsag.set(fig)

        return fig

    @reactive.effect
    @reactive.event(input.download_plot_gridsag)
    def download_plot_gridsag():
        req(config.get().sections())
        req(input.do_plot_gridsag())
        modal_download("plot_gridsag", "pdf")

    @render.download
    def download_plot_gridsag_pdf():
        outfile: list[FileInfo] | None = input.save_pdf()

        figure_gridsag.get().savefig(cache / outfile)

        return os.path.join(os.path.dirname(__file__), "cache", outfile)

    @reactive.effect
    @reactive.event(input.open_ini)
    def open_ini():
        # async def open_ini():
        req(input.open_ini())
        file: list[FileInfo] | None = input.open_ini()

        if file is None:
            return

        if not file[0]["name"].endswith(".ini"):
            logger.error("Invalid file")
            return

        if ini_file.get().endswith(".ini") and ini_file.get() != file[0]["name"]:
            return
            # await session.send_custom_message("refresh", "")

        ini_file.set(file[0]["datapath"])
        config.get().read(ini_file.get())

        (
            general_elems,
            sim_elems,
            field_elems,
            wl_elems,
            lens_elems,
            wfe_elems,
            analysis_sidebar_elems,
            analysis_elems,
        ) = app_elems(config.get())

        (
            Zernike_sidebar_elems,
            Zernike_elems,
            Zernike_tab_elems,
            PSD_sidebar_elems,
            PSD_elems,
            PSD_tab_elems,
            gridsag_sidebar_elems,
            gridsag_elems,
            gridsag_tab_elems,
        ) = wfe_elems

        refresh_ui("general", general_elems)
        refresh_ui("sim", sim_elems)
        refresh_ui("field", field_elems, mode="dict")
        refresh_ui("wl", wl_elems, mode="dict")
        refresh_ui("lens", lens_elems, mode="dict")
        refresh_ui("Zernike_settings", Zernike_sidebar_elems)
        if Zernike_elems:
            for key, _ in Zernike_elems.items():
                refresh_ui("zernike", Zernike_elems, mode="nested-dict", key=key)
        refresh_ui("Zernike_tab", Zernike_tab_elems)
        refresh_ui("PSD_settings", PSD_sidebar_elems)
        if PSD_elems:
            for key, _ in PSD_elems.items():
                refresh_ui("PSD", PSD_elems, mode="nested-dict", key=key)
        refresh_ui("PSD_tab", PSD_tab_elems)
        refresh_ui("gridsag_settings", gridsag_sidebar_elems)
        if gridsag_elems:
            for key, _ in gridsag_elems.items():
                refresh_ui("gridsag", gridsag_elems, mode="nested-dict", key=key)
        refresh_ui("gridsag_tab", gridsag_tab_elems)
        refresh_ui("analysis_settings", analysis_sidebar_elems)
        refresh_ui("analysis", analysis_elems)

        with open(cache / "tmp.ini", "w", encoding="utf-8") as f:
            config.get().write(f)

    @reactive.effect
    @reactive.event(input.close)
    async def _():
        await session.close()


app_dir = Path(__file__).parent
www = app_dir / "www"
cache = app_dir / "cache"
Path(www).mkdir(exist_ok=True, parents=True)
Path(cache).mkdir(exist_ok=True, parents=True)
app = App(app_ui, server, debug=False, static_assets=www)
