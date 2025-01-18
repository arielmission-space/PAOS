import marimo

__generated_with = "0.10.7"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md("""# Plot refractive index""")
    return


@app.cell
def _(Material, mo):
    _mat = Material(wl=1.0)

    material = mo.ui.dropdown(_mat.materials.keys(), label="Choose material")
    return (material,)


@app.cell
def _(mo):
    tamb = mo.ui.slider(
        start=-273, stop=25, step=1, value=-218, label="Ambient T [C]"
    )
    pamb = mo.ui.slider(
        start=0, stop=10, step=0.1, value=1, label="Ambient P [atm]"
    )
    return pamb, tamb


@app.cell
def _(material, mo, pamb, tamb):
    mo.vstack(
        [
            material,
            mo.hstack([tamb, mo.md(f"{tamb.value}")]),
            mo.hstack([pamb, mo.md(f"{pamb.value}")]),
        ],
        align="start",
    )
    return


@app.cell
def _(mo):
    wlmin = mo.ui.text(value="0.5", label=r"wl$_{min}$")
    wlmax = mo.ui.text(value="7.8", label=r"wl$_{max}$")
    Nwl = mo.ui.number(value=100, label=r"N$_{wl}$", step=1)

    mo.vstack(
        [wlmin, wlmax, Nwl],
    )
    return Nwl, wlmax, wlmin


@app.cell
def _(material, mo, np, plot_n, wlmax, wlmin):
    mo.stop(float(wlmin.value) >= float(wlmax.value))
    mo.stop(np.logical_or(float(wlmin.value) <= 0, float(wlmax.value) <= 0))
    mo.stop(material.value is None)

    plot_n(material.value)
    return


@app.cell
def _(Material, Nwl, np, pamb, plt, tamb, wlmax, wlmin):
    def plot_n(name):
        mat = Material(
            wl=np.linspace(float(wlmin.value), float(wlmax.value), Nwl.value),
            Tambient=tamb.value,
            Pambient=pamb.value,
        )
        nmat0, nmat = mat.nmat(name)

        plt.figure()
        plt.plot(mat.wl, nmat0, "--", label=r"T$_{\mathrm{ref}}$")
        plt.plot(mat.wl, nmat, label=r"T$_{\mathrm{amb}}$")
        plt.xlabel(r"Wavelength [$\bf{\mu}$m]")
        plt.ylabel("Relative index")
        plt.legend()
        plt.title(name.capitalize())
        plt.grid()

        return plt.gca()
    return (plot_n,)


@app.cell
def _():
    import marimo as mo

    from paos.util.material import Material
    import numpy as np
    import matplotlib.pyplot as plt
    return Material, mo, np, plt


if __name__ == "__main__":
    app.run()
