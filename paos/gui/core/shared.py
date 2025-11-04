import configparser

import faicons as fa
import numpy as np
from shiny import ui

ICONS = {
    "ellipsis": fa.icon_svg("ellipsis"),
    "gear": fa.icon_svg("gear"),
    "open": fa.icon_svg("folder-open"),
    "save": fa.icon_svg("floppy-disk"),
    "close": fa.icon_svg("xmark"),
    "docs": fa.icon_svg("book-open-reader"),
    "about": fa.icon_svg("info"),
    "run": fa.icon_svg("play"),
    "refresh": fa.icon_svg("arrows-rotate"),
    "info": fa.icon_svg("circle-info"),
    "load": fa.icon_svg("cloud-arrow-up"),
    "download": fa.icon_svg("cloud-arrow-down"),
    "wizard": fa.icon_svg("hat-wizard"),
}

CARD_HEADER_CLASS = "d-flex justify-content-between align-items-center"

vline = ui.HTML(
    """
    <div style="border-right: 0.1px solid lightgrey; height: 100%;"></div>
    """
)

hline = ui.HTML(
    """
    <div style="border-bottom: 0.1px solid lightgrey; width: 100%;"></div>
    """
)


vspace = ui.tags.div(style="height: 15px;")


def menu_panel(id):
    return ui.nav_panel(
        ui.input_action_button(
            id,
            id.capitalize(),
            icon=ICONS[id],
            width="100%",
        )
    )


def fill_value(items, name, row, col):
    func = items[name]["f"]
    prefix = "" if "prefix" not in items[name] else items[name]["prefix"]
    theid = f"{prefix}{name}_{row}_{col}"
    if func in [ui.input_select]:
        return func(
            id=theid,
            label=items[name]["label"] if "label" in items[name] else "",
            choices=items[name]["choices"],
            selected=items[name]["selected"],
        )
    elif func in [ui.tags.input]:
        return func(
            id=theid,
            type="text",
            value=items[name]["value"],
            readonly=items[name]["readonly"],
            class_="form-control",
        )
    elif func in [ui.input_text]:
        return func(
            id=theid,
            label=items[name]["label"] if "label" in items[name] else "",
            value=items[name]["value"],
            placeholder=(
                items[name]["placeholder"] if "placeholder" in items[name] else ""
            ),
        )
    elif func in [ui.input_checkbox]:
        return func(
            id=theid,
            label=items[name]["label"] if "label" in items[name] else "",
            value=items[name]["value"],
        )
    elif func in [ui.popover]:
        return (
            func(
                ICONS["gear"],
                ui.div(
                    *[
                        fill_value(items[name]["value"], key, row, col)
                        for key in items[name]["value"].keys()
                    ],
                ),
                title=items[name]["title"],
                placement="top",
            ),
        )
    elif func in [ui.p]:
        return func(
            f"{items[name]['value']}",
        )
    elif func in [ui.navset_card_pill]:
        return func(
            ui.nav_panel(
                items[name]["title"],
                ui.div(
                    *[
                        fill_value(items[name]["value"], key, row, col)
                        for key in items[name]["value"].keys()
                    ],
                ),
            ),
            selected=False,
        )
    elif func in [ui.accordion]:
        return func(
            ui.accordion_panel(
                items[name]["title"],
                ui.div(
                    *[
                        fill_value(items[name]["value"], key, row, col)
                        for key in items[name]["value"].keys()
                    ],
                ),
            ),
            open=False,
        )
    elif func in [ui.card]:
        return func(
            ui.div(
                items[name]["title"],
                ui.div(
                    *[
                        fill_value(items[name]["value"], key, row, col)
                        for key in items[name]["value"].keys()
                    ],
                ),
            ),
            open=False,
        )


def fill_header(items):
    if not items:
        return ui.div()
    key = min(np.array(list(items.keys())))
    item = items[key]
    return ui.div(
        {"style": "display: flex;"},
        *[
            ui.column(
                subitem["width"],
                {"style": "text-align: center;"},
                ui.markdown(f"**{subkey}**"),
                hline,
            )
            for _, (subkey, subitem) in enumerate(item.items())
        ],
    )


def fill_body(items):
    if not items:
        return [ui.div()]
    return [
        ui.div(
            {"style": "display: flex;"},
            *[
                ui.column(
                    subitem["width"],
                    {"style": "text-align: center;"},
                    fill_value(item, subkey, row + 1, col),
                )
                for col, (subkey, subitem) in enumerate(item.items())
            ],
        )
        for row, (_, item) in enumerate(items.items())
    ]


def refresh_ui(name, items, mode=None, key=""):
    ui.remove_ui(f"#inserted-{name}-editor")

    func = ui.div

    if mode == "dict":
        items = [fill_header(items), *fill_body(items)]
        func = ui.card

    elif mode == "nested-dict":
        key = list(items.keys())[0] if key == "" else key
        items = [fill_header(items[key]), *fill_body(items[key])]
        func = ui.card

    elif mode == "body":
        items = [*fill_body(items)]

    elif mode == "header":
        items = [*fill_body(items)]

    ui.insert_ui(
        func(
            {"id": f"inserted-{name}-editor"},
            *items,
        ),
        selector=f"#{name}-editor",
        where="beforeEnd",
    )


def to_configparser(dictionary):
    """
    Given a dictionary, it converts it into a :class:`~configparser.ConfigParser` object

    Parameters
    ----------
    dictionary: dict
        input dictionary to be converted

    Returns
    -------
    out: :class:`~configparser.ConfigParser`
    """

    config = configparser.ConfigParser()

    for key, item in dictionary.items():
        if isinstance(item, dict):
            config.add_section(key)
            for subkey, subitem in item.items():
                if subitem is not None and subitem != "":
                    if isinstance(subitem, str):
                        pass
                    elif isinstance(subitem, (float, bool)):
                        subitem = str(subitem)
                    elif isinstance(subitem, (tuple, list)):
                        subitem = ",".join(subitem)
                    else:
                        raise NotImplementedError("item type not supported")
                config.set(key, subkey, subitem)

    return config


def ellipsis(id, names, choices):
    return ui.popover(
        ICONS["ellipsis"],
        *[
            ui.input_select(
                id=f"{id}_select_{name}",
                label=f"Select {name.capitalize()}",
                choices=choice,
            )
            for name, choice in zip(names, choices)
        ],
        title="",
        placement="top",
    )


def output_text_verbatim(id, placeholder=True):
    return ui.div(
        {"id": f"{id}-editor"},
        ui.div(
            {"id": f"inserted-{id}-editor"},
            ui.output_text_verbatim(
                id,
                placeholder=placeholder,
            ),
        ),
    )


def modal_download(id, ext):
    m = ui.modal(
        *[
            ui.input_text(
                id=f"save_{ext}",
                label="Save As",
                value=f"filename.{ext}",
                placeholder=f"filename.{ext}",
            ),
            ui.download_button(
                f"download_{id}_{ext}",
                "Download",
                icon=ICONS["download"],
                class_="btn-success",
            ),
            # ui.output_text_verbatim(f"download_{ext}_progress"),
        ],
        title=f"Save to {ext.upper()} File",
        easy_close=True,
    )
    ui.modal_show(m)


def nested_div(id):
    return ui.div(
        {"id": f"{id}-editor"},
        ui.div(
            {"id": f"inserted-{id}-editor"},
        ),
    )
