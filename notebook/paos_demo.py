import marimo

__generated_with = "0.10.7"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md(r"""# PAOS demo""")
    return


@app.cell
def _(mo):
    mo.md(r"""## Select .ini config file""")
    return


@app.cell
def _(mo, os):
    file_path = "../lens data/"

    mo.stop(not os.path.isdir(file_path))

    file_browser = mo.ui.file_browser(
        initial_path=file_path,
        multiple=False,
    )

    file_browser
    return file_browser, file_path


@app.cell
def _(mo):
    mo.md(r"""## Set field and wavelength""")
    return


@app.cell
def _(mo):
    field_s = mo.ui.text("0.0", label=r"Field x [$^{\circ}$]")
    field_t = mo.ui.text("0.0", label=r"Field y [$^{\circ}$]")

    mo.hstack([field_s, field_t], justify="start")
    return field_s, field_t


@app.cell
def _(mo):
    wavelength = mo.ui.text("1.55", label=r"Wavelength [$\mu$m]")

    wavelength
    return (wavelength,)


@app.cell
def _(mo):
    mo.md(r"""## Play with PAOS""")
    return


@app.cell
def _(compute_raytrace, file_browser, mo):
    mo.stop(file_browser.path() is None)

    mo.accordion(
        {"### Paraxial raytrace": mo.ui.table(compute_raytrace())},
        lazy=True,
    )
    return


@app.cell
def _(get_surf_info, mo, plot, retval, surf):
    mo.stop(surf.value is None)

    mo.accordion(
        {
            "### POP": mo.vstack(
                [
                    mo.hstack(
                        [surf, get_surf_info(int(surf.value))],
                        justify="start",
                    ),
                    plot(retval, int(surf.value)),
                ]
            )
        },
        lazy=True,
    )
    return


@app.cell
def _(compute_pop, file_browser, mo, np):
    mo.stop(file_browser.path() is None)

    retval = compute_pop()
    keys = np.array(list(retval.keys())).astype(str)

    surf = mo.ui.dropdown(keys, value=keys[-1], label="Plot surf")
    return keys, retval, surf


@app.cell
def _(
    configparser,
    field_s,
    field_t,
    file_browser,
    os,
    parse_config,
    plt,
    raytrace,
    run,
    simple_plot,
    tempfile,
    wavelength,
):
    def get_surf_info(id_surf):
        config = configparser.ConfigParser()
        config.read(file_browser.path())

        return config[f"lens_{id_surf:02d}"]["comment"]


    def update_config():
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, file_browser.name())

        config = configparser.ConfigParser()
        config.read(file_browser.path())
        config["wavelengths"]["w1"] = wavelength.value
        config["fields"]["f1"] = ",".join([field_s.value, field_t.value])

        with open(temp_file_path, "w") as f:
            config.write(f)

        pup_diameter, parameters, wavelengths, fields, opt_chains = parse_config(
            temp_file_path,
        )

        return pup_diameter, parameters, wavelengths, fields, opt_chains


    def compute_raytrace():
        pup_diameter, parameters, wavelengths, fields, opt_chains = update_config()

        rt = raytrace(fields[0], opt_chains[0])

        res = {}
        res["Surface key"] = [item.split(" - ")[0] for item in rt]
        res["Description"] = [item.split(" - ")[1].split("y:")[0] for item in rt]
        res["Sagittal data [x]"] = ["x: " + item.split("x:")[1] for item in rt]
        res["Tangential data [y]"] = [
            "y: " + item.split("y:")[1].split("x:")[0] for item in rt
        ]

        return res


    def compute_pop():
        pup_diameter, parameters, wavelengths, fields, opt_chains = update_config()

        return run(
            pup_diameter,
            1.0e-6 * wavelengths[0],
            parameters["grid_size"],
            parameters["zoom"],
            fields[0],
            opt_chains[0],
        )


    def plot(retval, id_surf):
        fig = plt.figure()
        ax = plt.gca()
        simple_plot(fig, ax, id_surf, retval[id_surf], ima_scale="log")

        return ax
    return compute_pop, compute_raytrace, get_surf_info, plot, update_config


@app.cell
def _():
    import marimo as mo

    import os
    import time
    import configparser
    import tempfile
    import numpy as np
    import matplotlib.pyplot as plt

    from paos.core.parseConfig import parse_config
    from paos.core.raytrace import raytrace
    from paos.core.run import run
    from paos.gui.core.plot import simple_plot

    from paos.log.logger import setLogLevel

    setLogLevel(level="INFO")
    return (
        configparser,
        mo,
        np,
        os,
        parse_config,
        plt,
        raytrace,
        run,
        setLogLevel,
        simple_plot,
        tempfile,
        time,
    )


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
