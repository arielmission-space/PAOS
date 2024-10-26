from shiny import ui
from .shared import nested_div
from .shared import menu_panel


menu_items = [
    ui.nav_menu("File", menu_panel("open"), menu_panel("save"), menu_panel("close")),
    ui.nav_menu("Help", menu_panel("docs"), menu_panel("about")),
]

sidebar_items = [
    ui.accordion_panel("General", nested_div("general")),
    ui.accordion_panel("Units", nested_div("units")),
    ui.accordion_panel("Simulation", nested_div("sim")),
    ui.accordion_panel("Fields", nested_div("field")),
    ui.accordion_panel("Wavelengths", nested_div("wl")),
]

main_items = [
    ui.nav_panel("Lens Editor", nested_div("lens")),
    ui.nav_panel(
        "Zernike Editor",
        ui.layout_columns(
            ui.div(
                ui.card(nested_div("zernike_explorer"), full_screen=True),
            ),
            ui.card(nested_div("zernike_plots"), full_screen=True),
        ),
    ),
    ui.nav_panel(
        "Analysis",
        ui.layout_columns(
            ui.div(
                ui.card(nested_div("pop"), full_screen=True),
                ui.card(nested_div("raytrace"), full_screen=True),
            ),
            ui.card(nested_div("plots"), full_screen=True),
        ),
    ),
]
