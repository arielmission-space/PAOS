import os
import time
import configparser
from pathlib import Path
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
from paos import __pkg_name__
from paos import __version__
from paos import __author__
from paos import __license__
from paos.core.parseConfig import parse_config

from core.shared import refresh_ui
from core.shared import modal_download
from core.appio import to_ini
from core.elems import app_elems
from core.items import menu_items
from core.items import sidebar_items
from core.items import main_items
from core.plot import simple_plot
from core.plot import zernike_plot


page_dependencies = ui.tags.head(
    ui.tags.link(rel="stylesheet", type="text/css", href="layout.css"),
)


def app_ui(request: StarletteRequest) -> Tag:
    return ui.page_fillable(
        page_dependencies,
        ui.tags.script(
            """
        Shiny.addCustomMessageHandler('refresh', function(message) {
            window.location.reload();
        });
        """,
        ),
        ui.tags.div(
            ui.tags.div(
                ui.navset_pill(*menu_items, selected=True),
                _class="navigation-menu",
            ),
            ui.tags.div(
                ui.tags.a(
                    ui.tags.img(src="static/logo.png", height="50px"),
                    href="https://github.com/arielmission-space/PAOS",
                ),
                id="logo-top",
                class_="navigation-logo",
            ),
            id="div-navbar",
            class_="navbar-top",
        ),
        ui.markdown("___"),
        ui.layout_sidebar(
            ui.sidebar(
                ui.p("System Explorer"),
                ui.accordion(*sidebar_items, open=False),
            ),
            ui.navset_card_pill(
                id="main",
                *main_items,
            ),
        ),
        title="PAOS GUI",
    )


def server(input, output, session):
    ini_file = reactive.value("filename")
    config = reactive.value(configparser.ConfigParser())
    retval = reactive.value({})
    figure = reactive.value(None)
    figure_zernike = reactive.value(None)

    for file in os.listdir(cache):
        os.remove(os.path.join(cache, file))

    @reactive.effect
    @reactive.event(input.save, input.calc_raytrace, input.calc_pop)
    def _():
        req(input.save)
        req(input.calc_raytrace)
        to_ini(input=input, config=config, tmp=cache / "tmp.ini")

    @reactive.calc
    def calc_raytrace():
        req(config.get().sections())
        req(input.raytrace_select_field())
        req(input.raytrace_select_wl())

        field = input.raytrace_select_field()
        wl = input.raytrace_select_wl()

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
        print(f"Downloaded {outfile}")

        with open(cache / outfile, "w") as f:
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

        field = input.raytrace_select_field()
        wl = input.raytrace_select_wl()

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
        req(input.pop_select_field())
        req(input.pop_select_wl())

        field = input.pop_select_field()
        wl = input.pop_select_wl()

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

        field = input.pop_select_field()
        wl = input.pop_select_wl()

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

        with open(cache / "tmp.ini", "r") as f:
            with open(cache / outfile, "w") as cf:
                cf.write(f.read())

        return os.path.join(os.path.dirname(__file__), "cache", outfile)

    @reactive.effect
    @reactive.event(input.docs)
    def _():
        req(input.docs())
        m = ui.modal(
            ui.markdown(
                f"Click [here](https://paos.readthedocs.io/en/latest/) to access the {__pkg_name__.upper()} documentation."
            ),
            title="Documentation",
            easy_close=True,
        )
        ui.modal_show(m)

    @reactive.effect
    @reactive.event(input.about)
    def _():
        req(input.about())
        m = ui.modal(
            ui.markdown(
                f"SOFTWARE: {__pkg_name__.upper()} v{__version__}  \n"
                f"AUTHOR: {__author__}  \n"
                f"LICENSE: {__license__}  \n"
            ),
            title="About",
            easy_close=True,
        )
        ui.modal_show(m)

    @reactive.effect
    @reactive.event(input.docs)
    def _():
        req(input.docs())
        m = ui.modal(
            ui.markdown(
                """
                Click [here](https://paos.readthedocs.io/en/latest/) to access the PAOS documentation.
                """
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
                    "Example files can be found in the PAOS public [GitHub repository](https://github.com/arielmission-space/PAOS)."
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
    @reactive.event(input.open_ini, input.zernike_select_surface)
    def zernike_inputs():
        req(config.get().sections())
        req(input.zernike_select_surface())

        refresh_ui(
            "zernike_inputs",
            [ui.output_text_verbatim("zernike_inputs", placeholder=True)],
        )

        surface = input.zernike_select_surface()

        (_, _, _, _, _, _, _, zernike_elems, _, _, _, _) = app_elems(config.get())

        surface_key = int(surface[1:])
        refresh_ui("zernike", zernike_elems, mode="nested-dict", key=surface_key)

        return f"Surface: {surface}"

    @render.plot(alt="Zernike plot")
    @reactive.event(input.do_plot_zernike)
    def plot_zernike():
        req(input.do_plot_zernike())
        req(input.zernike_plot_select_surface())
        req(config.get().sections())

        to_ini(input=input, config=config, tmp=cache / "tmp.ini")

        surface = input.zernike_plot_select_surface()
        surface_key = int(surface[1:])
        zernike_section = f"lens_{surface_key:02d}"
        zernike_section = config.get()[zernike_section]

        zindex = zernike_section.get("zindex").split(",")
        zindex = list(map(int, zindex))
        zcoeffs = zernike_section.get("z").split(",")
        zcoeffs = list(map(float, zcoeffs))
        wavelength = float(zernike_section.get("par1"))
        ordering = zernike_section.get("par2")
        normalize = bool(zernike_section.get("par3"))

        fig, ax = plt.subplots()
        zernike_plot(
            fig=fig,
            axis=ax,
            surface=surface,
            index=zindex,
            Z=zcoeffs,
            wavelength=wavelength,
            ordering=ordering,
            normalize=normalize,
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
    def download_plot_zernike_pdf():
        outfile: list[FileInfo] | None = input.save_pdf()

        figure_zernike.get().savefig(cache / outfile)

        return os.path.join(os.path.dirname(__file__), "cache", outfile)

    @render.text
    @reactive.event(input.do_plot_zernike)
    def plot_zernike_inputs():
        req(input.do_plot_zernike())

        refresh_ui(
            "plot_zernike_inputs",
            [ui.output_text_verbatim("plot_zernike_inputs", placeholder=True)],
        )

        surface = input.zernike_plot_select_surface()

        return f"Surface: {surface}"

    @reactive.effect
    @reactive.event(input.open_ini)
    # async def open_ini():
    def open_ini():
        req(input.open_ini())
        file: list[FileInfo] | None = input.open_ini()

        if file is None:
            return

        if not file[0]["name"].endswith(".ini"):
            print("Invalid file")
            return

        if ini_file.get().endswith(".ini") and ini_file.get() != file[0]["name"]:
            return
            # await session.send_custom_message("refresh", "")

        ini_file.set(file[0]["datapath"])
        config.get().read(ini_file.get())

        (
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
        ) = app_elems(config.get())

        refresh_ui("general", general_elems)
        refresh_ui("units", units_elems)
        refresh_ui("sim", sim_elems)
        refresh_ui("field", field_elems, mode="dict")
        refresh_ui("wl", wl_elems, mode="dict")
        refresh_ui("lens", lens_elems, mode="dict")
        refresh_ui("zernike_explorer", zernike_explorer_elems)
        if zernike_elems:
            for key in zernike_elems.keys():
                refresh_ui("zernike", zernike_elems, mode="nested-dict", key=key)
        refresh_ui("zernike_plots", zernike_plots_elems)
        refresh_ui("pop", pop_elems)
        refresh_ui("raytrace", raytrace_elems)
        refresh_ui("plots", plots_elems)

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