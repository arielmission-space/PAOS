import faicons as fa
from shiny import ui
import configparser
import numpy as np

ICONS = {
    "ellipsis": fa.icon_svg("ellipsis"),
    "open": fa.icon_svg("folder-open"),
    "save": fa.icon_svg("floppy-disk"),
    "close": fa.icon_svg("xmark"),
    "docs": fa.icon_svg("book-open-reader"),
    "about": fa.icon_svg("info"),
    "run": fa.icon_svg("play"),
}

card_header_class_ = "d-flex justify-content-between align-items-center"


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
    elif func in [ui.input_text, ui.input_checkbox]:
        return func(
            id=theid,
            label=items[name]["label"] if "label" in items[name] else "",
            value=items[name]["value"],
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
                ui.markdown(
                    f"**{subkey}**  \n" "___",
                ),
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
        for row, (key, item) in enumerate(items.items())
    ]


def refresh_ui(name, items, mode=None, key=""):
    ui.remove_ui(f"#inserted-{name}-editor")

    if mode == "dict":
        items = [fill_header(items), *fill_body(items)]

    elif mode == "nested-dict":
        key = list(items.keys())[0] if key == "" else key
        items = [fill_header(items[key]), *fill_body(items[key])]

    ui.insert_ui(
        ui.div(
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
                id=f"{id}_select_{name}", label=f"Choose {name}", choices=choice
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
                "Save",
            ),
            ui.output_text(f"download_{ext}_progress"),
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